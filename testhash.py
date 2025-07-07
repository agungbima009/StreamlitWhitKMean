import bcrypt

# Jawaban pertanyaan keamanan
security_answer = "nalakomikucingku"

# Proses hashing
hashed_answer = bcrypt.hashpw(security_answer.encode('utf-8'), bcrypt.gensalt())

# Convert menjadi string agar bisa disimpan di JSON
hashed_answer_str = hashed_answer.decode('utf-8')

print("Hashed Security Answer:")
print(hashed_answer_str)
