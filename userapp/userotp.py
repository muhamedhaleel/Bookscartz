import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings

def generateAndSendOtp(toEmail, length=6):
    
    def generateOtp(length):
        otp = ''.join([str(random.randint(0,9)) for _ in range(length)])
        
        return otp
    
    def sentEmail(toEmail,otp):
        fromEmail = settings.EMAIL_HOST_USER
        fromPassword = settings.EMAIL_HOST_PASSWORD
        
        msg = MIMEMultipart()
        msg['From'] = fromEmail
        msg['To'] = toEmail
        msg['subject'] = 'YOUR OTP CODE '
        
        body = f"YOUR OTP CODE IS {otp}"
        msg.attach(MIMEText(body,'plain'))  
        
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(fromEmail, fromPassword)
            text = msg.as_string()
            server.sendmail(fromEmail, toEmail, text)
            server.quit()
            print(f"Email sent successfully to {toEmail}")
            print(f"Generated OTP: {otp}")
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            
    otp = generateOtp(length)
    print(f"Generated OTP before sending: {otp}")
    
    sentEmail(toEmail,otp)
    return otp