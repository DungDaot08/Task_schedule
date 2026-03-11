import bcrypt

password = "123"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

print(f"""
INSERT INTO users(username,password)
VALUES('admin','{hashed}');
""")
