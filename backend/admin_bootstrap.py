"""
Secure admin bootstrapping for production deployments.
Automatically creates initial admin user from environment variables on first startup.
"""
import os
import logging
from sqlalchemy.orm import Session

from db.base import SessionLocal
from db.models import UserDB, UserRole, pwd_context, truncate_password_for_bcrypt

logger = logging.getLogger(__name__)


def bootstrap_admin_user() -> bool:
    """
    Bootstrap initial admin user from environment variables if no admin exists.

    This runs automatically on application startup and creates an admin user
    only if:
    1. INITIAL_ADMIN_USERNAME, INITIAL_ADMIN_EMAIL, INITIAL_ADMIN_PASSWORD are set
    2. No admin user exists in the database yet

    Returns:
        bool: True if admin was created, False if skipped

    Security Notes:
        - Only runs if no admin exists (one-time bootstrap)
        - Credentials should be in .env (NOT in code)
        - .env file should NEVER be committed to git
        - After first login, admin should change password via UI
        - Set strong password in INITIAL_ADMIN_PASSWORD (min 16 chars recommended)
    """
    # Get credentials from environment
    admin_username = os.getenv("INITIAL_ADMIN_USERNAME")
    admin_email = os.getenv("INITIAL_ADMIN_EMAIL")
    admin_password = os.getenv("INITIAL_ADMIN_PASSWORD")

    # If any credential is missing, skip bootstrap
    if not all([admin_username, admin_email, admin_password]):
        logger.info("Admin bootstrap skipped: INITIAL_ADMIN_* environment variables not set")
        return False

    # Validate password strength
    if len(admin_password) < 12:
        logger.error("Admin bootstrap failed: INITIAL_ADMIN_PASSWORD must be at least 12 characters")
        return False

    db: Session = SessionLocal()
    try:
        # Check if any admin user already exists
        existing_admin = db.query(UserDB).filter(UserDB.role == UserRole.ADMIN).first()

        if existing_admin:
            logger.info("Admin bootstrap skipped: Admin user already exists")
            return False

        # Check if username or email already taken
        existing_user = db.query(UserDB).filter(
            (UserDB.username == admin_username) | (UserDB.email == admin_email)
        ).first()

        if existing_user:
            logger.error(
                f"Admin bootstrap failed: Username '{admin_username}' or "
                f"email '{admin_email}' already exists"
            )
            return False

        # Hash password
        password_truncated = truncate_password_for_bcrypt(admin_password)
        hashed_password = pwd_context.hash(password_truncated)

        # Create admin user
        admin_user = UserDB(
            username=admin_username,
            email=admin_email,
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            is_active=True
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        logger.info("="*60)
        logger.info("🎉 Initial admin user created successfully!")
        logger.info("="*60)
        logger.info(f"Username: {admin_user.username}")
        logger.info(f"Email: {admin_user.email}")
        logger.info(f"Role: {admin_user.role}")
        logger.info(f"User ID: {admin_user.id}")
        logger.info("")
        logger.info("⚠️  SECURITY RECOMMENDATION:")
        logger.info("   1. Login with these credentials")
        logger.info("   2. Change password immediately via UI")
        logger.info("   3. Remove INITIAL_ADMIN_* from .env after first login")
        logger.info("="*60)

        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Admin bootstrap failed: {str(e)}")
        return False
    finally:
        db.close()


def ensure_admin_exists() -> None:
    """
    Ensure at least one admin user exists in the system.

    This is a safety check that runs on startup. If no admin exists
    and INITIAL_ADMIN_* variables are set, it will create one.

    Raises:
        RuntimeError: If no admin exists and bootstrap variables are not set
    """
    db: Session = SessionLocal()
    try:
        admin_count = db.query(UserDB).filter(UserDB.role == UserRole.ADMIN).count()

        if admin_count == 0:
            logger.warning("No admin users found in database")

            # Try to bootstrap
            if bootstrap_admin_user():
                logger.info("Admin user bootstrapped successfully")
            else:
                # If bootstrap failed/skipped, this is a critical issue
                logger.error("")
                logger.error("="*60)
                logger.error("⚠️  CRITICAL: No admin users exist!")
                logger.error("="*60)
                logger.error("")
                logger.error("To create an initial admin user, set these environment variables:")
                logger.error("  INITIAL_ADMIN_USERNAME=your_admin_username")
                logger.error("  INITIAL_ADMIN_EMAIL=admin@example.com")
                logger.error("  INITIAL_ADMIN_PASSWORD=your_secure_password_min_12_chars")
                logger.error("")
                logger.error("Then restart the application.")
                logger.error("="*60)

                # Don't raise error - allow app to start but log warning
                # raise RuntimeError("No admin users exist and admin bootstrap failed")
        else:
            logger.info(f"Admin check: {admin_count} admin user(s) found")

    finally:
        db.close()
