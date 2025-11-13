"""
Tabel Detector en Parser
Detecteert en extraheert tabellen uit tekst voor betere rendering.
"""
import re
from typing import List, Dict, Optional, Tuple
import pandas as pd


class TableDetector:
    """
    Detecteert tabellen in tekst en converteert ze naar gestructureerde data.
    """

    def detect_tables(self, text: str) -> List[Dict]:
        """
        Detecteer alle tabellen in een tekst.

        Args:
            text: Tekst om te analyseren

        Returns:
            List van table dicts met:
            - type: "markdown" of "plain"
            - start_pos: Start positie in tekst
            - end_pos: Eind positie in tekst
            - content: Originele tabel tekst
            - parsed_data: DataFrame of None
        """
        tables = []

        # Detecteer markdown tabellen
        markdown_tables = self._detect_markdown_tables(text)
        tables.extend(markdown_tables)

        # Detecteer plain text tabellen (met whitespace alignment)
        # TODO: Implement if needed

        return tables

    def _detect_markdown_tables(self, text: str) -> List[Dict]:
        """
        Detecteer markdown tabellen in tekst.

        Markdown tabel formaat:
        | Header 1 | Header 2 |
        |----------|----------|
        | Cell 1   | Cell 2   |

        Args:
            text: Tekst om te analyseren

        Returns:
            List van tabel dicts
        """
        tables = []

        # Regex pattern voor markdown tabellen
        # Match: lines starting with | and containing |
        lines = text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check if line looks like markdown table
            if line.startswith('|') and line.endswith('|') and line.count('|') >= 3:
                # Potential table start
                table_lines = []
                table_start_idx = i

                # Collect all consecutive table lines
                while i < len(lines):
                    current_line = lines[i].strip()
                    if current_line.startswith('|') and current_line.endswith('|'):
                        table_lines.append(current_line)
                        i += 1
                    else:
                        break

                # Validate: must have at least 3 lines (header, separator, data)
                if len(table_lines) >= 3:
                    # Check if second line is separator (contains only |, -, :, and spaces)
                    separator_line = table_lines[1]
                    if re.match(r'^[\|\-\:\s]+$', separator_line):
                        # Valid markdown table
                        table_content = '\n'.join(table_lines)

                        # Parse to DataFrame
                        df = self._parse_markdown_table(table_lines)

                        tables.append({
                            "type": "markdown",
                            "line_start": table_start_idx,
                            "line_end": i - 1,
                            "content": table_content,
                            "parsed_data": df
                        })
                    else:
                        i += 1
                else:
                    i += 1
            else:
                i += 1

        return tables

    def _parse_markdown_table(self, table_lines: List[str]) -> Optional[pd.DataFrame]:
        """
        Parse markdown tabel naar pandas DataFrame.

        Args:
            table_lines: Lines van de markdown tabel

        Returns:
            DataFrame of None bij parse fout
        """
        try:
            # Extract header
            header_line = table_lines[0]
            headers = [cell.strip() for cell in header_line.split('|')[1:-1]]

            # Skip separator line (line 1)

            # Extract data rows
            data_rows = []
            for line in table_lines[2:]:  # Skip header and separator
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(cells) == len(headers):
                    data_rows.append(cells)

            if not data_rows:
                return None

            # Create DataFrame
            df = pd.DataFrame(data_rows, columns=headers)
            return df

        except Exception as e:
            # Parse failed
            return None

    def replace_tables_with_placeholder(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Vervang tabellen in tekst met placeholders voor betere rendering.

        Args:
            text: Originele tekst

        Returns:
            (modified_text, tables)
            - modified_text: Tekst met [TABLE_N] placeholders
            - tables: List van gedetecteerde tabellen
        """
        tables = self.detect_tables(text)

        if not tables:
            return text, []

        # Sort tables by position (reverse order for replacement)
        tables_sorted = sorted(tables, key=lambda t: t["line_start"], reverse=True)

        # Replace tables with placeholders
        lines = text.split('\n')
        for idx, table in enumerate(tables_sorted):
            table_id = len(tables_sorted) - idx - 1  # Original order
            placeholder = f"[TABLE_{table_id}]"

            # Remove table lines and insert placeholder
            start = table["line_start"]
            end = table["line_end"]

            # Keep lines before and after table
            before = lines[:start]
            after = lines[end + 1:]

            # Insert placeholder
            lines = before + [placeholder] + after

        modified_text = '\n'.join(lines)

        # Re-index tables with correct IDs
        for idx, table in enumerate(tables):
            table["table_id"] = idx

        return modified_text, tables

    def has_table(self, text: str) -> bool:
        """
        Check if tekst bevat een tabel.

        Args:
            text: Tekst om te checken

        Returns:
            True if tabel gevonden
        """
        tables = self.detect_tables(text)
        return len(tables) > 0


# Global instance
table_detector = TableDetector()
