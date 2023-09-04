class EmailService:
    async def sendEmail(self, email, content):
        print(f"To: {email}, content: {content}")
