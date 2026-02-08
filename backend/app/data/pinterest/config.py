class PinterestConfig:
    # ===========================
    # PINTEREST OAUTH
    # ===========================
    PINTEREST_APP_ID: str = "1543846"
    PINTEREST_APP_SECRET: str = "db774016ccd9aaa2805e688b39fd9055c581efcf"
    PINTEREST_REDIRECT_URI: str = "http://localhost:8081/auth/pinterest-callback"
    PINTEREST_FRONTEND_REDIRECT: str = "http://localhost:8081/onboarding"

    OAUTH_AUTHORIZE_URL: str = "https://www.pinterest.com/oauth/"
