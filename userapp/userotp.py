import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from decouple import config

def generateAndSendOtp(toEmail,length = 4):
    
    def generateOtp(length):
        otp = ''.join([str(random.randint(0,9)) for _ in range(length)])
        return otp
    
    def sentEmail(toEmail,otp):
        fromEmail = config('EMAIL_HOST_USER')
        fromPassword = config('EMAIL_HOST_PASSWORD')
        
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
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            
    otp = generateOtp(length)
    print(f"Genrated otp:{otp}")
    
    sentEmail(toEmail,otp)
    return otp