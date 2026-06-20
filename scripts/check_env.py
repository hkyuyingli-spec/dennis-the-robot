import os
import os.path as p

def main():
    print("Checking environment and credentials for Firebase/email tests:\n")
    print("SERVICE_ACCOUNT=" + ("FOUND" if p.exists("serviceAccountKey.json") else "MISSING"))
    print("GMAIL_USER=" + ("SET" if os.getenv("GMAIL_USER") else "UNSET"))
    print("GMAIL_PASSWORD=" + ("SET" if os.getenv("GMAIL_PASSWORD") else "UNSET"))
    print("NUTRIBOT_LANG=" + (os.getenv("NUTRIBOT_LANG") if os.getenv("NUTRIBOT_LANG") else "UNSET"))

if __name__ == '__main__':
    main()
