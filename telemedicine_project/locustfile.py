from locust import HttpUser, task, between
from random import randint, choice
import logging

# ✅ Setup Logging for Debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserLoadTest(HttpUser):
    """Simulates User Load Testing on the Authentication APIs."""
    
    host = "http://127.0.0.1:8001"  # ✅ Ensure this matches your Django server
    wait_time = between(2, 5)  # ✅ Prevents excessive load
    
    def on_start(self):
        """Runs when a new simulated user starts"""
        self.user_email = None
        self.access_token = None
        self.refresh_token = None

        self.user_email = self.register_user()
        if self.user_email:
            self.login_user()

    @task
    def register_user(self):
        """Simulates user registration with a valid role."""
        random_email = f"test{randint(100000, 999999)}@example.com"
        random_phone = f"9876{randint(100000, 999999)}"
        roles = ["doctor", "patient", "tmc"]
        selected_role = choice(roles)

        payload = {
            "email": random_email,
            "password": "Test@1234",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": random_phone,
            "role": selected_role  
        }

        response = self.client.post("/users/register/", json=payload)

        if response.status_code == 201:
            logger.info(f"✅ Registration Successful: {random_email} (Role: {selected_role})")
            return random_email  # ✅ Return email for login
        else:
            logger.warning(f"⚠️ Registration Failed! Status: {response.status_code} | Response: {response.text}")
            return None

    @task
    def login_user(self):
        """Simulates user login & stores token"""
        if not self.user_email:
            logger.warning("⚠️ Skipping Login: No user registered yet.")
            return

        payload = {"email": self.user_email, "password": "Test@1234"}
        response = self.client.post("/users/login/", json=payload)

        if response.status_code == 200:
            tokens = response.json().get("tokens", {})
            self.access_token = tokens.get("access", "")
            self.refresh_token = tokens.get("refresh", "")

            if self.access_token:
                self.client.headers.update({"Authorization": f"Bearer {self.access_token}"})
                logger.info(f"✅ Login Successful: {self.user_email} - Token Stored")
            else:
                logger.warning("⚠️ Login Failed: No Access Token Received")
        else:
            logger.error(f"⚠️ Login Failed! Status: {response.status_code} | Response: {response.text}")

    @task
    def get_profile(self):
        """Fetches user profile only if logged in."""
        if not self.access_token:
            logger.warning("⚠️ Skipping Profile Fetch: No access token available")
            return

        response = self.client.get("/users/profile/")

        if response.status_code == 200:
            logger.info(f"✅ Profile Fetched Successfully for {self.user_email}")
        else:
            logger.error(f"⚠️ Profile Fetch Failed! Status: {response.status_code} | Response: {response.text}")
            self.debug_profile_issue()

    @task
    def refresh_token_request(self):
        """Refreshes an access token using the stored refresh token."""
        if not self.refresh_token:
            logger.warning("⚠️ Skipping Refresh: No Refresh Token Available")
            return

        response = self.client.post("/users/token/refresh/", json={"refresh": self.refresh_token})

        if response.status_code == 200:
            new_access_token = response.json().get("access")
            if new_access_token:
                self.client.headers.update({"Authorization": f"Bearer {new_access_token}"})
                self.access_token = new_access_token  # ✅ Store new token
                logger.info(f"✅ Access Token Refreshed Successfully for {self.user_email}")
            else:
                logger.warning("⚠️ Refresh Failed: No New Access Token Received")
        else:
            logger.error(f"⚠️ Refresh Failed! Status: {response.status_code} | Response: {response.text}")

    @task
    def logout_user(self):
        """Logs out the user and removes stored tokens."""
        if not self.refresh_token:
            logger.warning("⚠️ Skipping Logout: No Refresh Token Available")
            return

        response = self.client.post("/users/logout/", json={"refresh_token": self.refresh_token})

        if response.status_code == 200:
            logger.info(f"✅ Logout Successful for {self.user_email}")
            self.access_token = None  # ✅ Remove stored token after logout
            self.refresh_token = None
        else:
            logger.error(f"⚠️ Logout Failed! Status: {response.status_code} | Response: {response.text}")

    def debug_profile_issue(self):
        """Logs additional debug information for profile fetching failures."""
        logger.debug("🛠 DEBUGGING PROFILE FETCH ISSUE")
        logger.debug(f"User Email: {self.user_email}")
        logger.debug(f"Stored Access Token: {self.access_token}")
