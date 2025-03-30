import os

# 🔹 Bot & Telegram API Details
API_ID = int(os.getenv("API_ID", 24740695))  # ⚠️ Yahan apna API_ID likho
API_HASH = os.getenv("API_HASH", "a95990848f2b93b8131a4a7491d97092")  # ⚠️ Yahan apna API_HASH likho
BOT_TOKEN = os.getenv("BOT_TOKEN", "7894506150:AAF98floEIulyeGU5zNwRy_TG4rx2c8EGgk")  # ⚠️ Yahan apna BOT_TOKEN likho

# 🔹 MongoDB Database URL
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://tsgcoder:tsgcoder@cluster0.1sodg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")  # ⚠️ Yahan apna MongoDB URL likho

# 🔹 Bot Developer & Group Info
DEVELOPER_USERNAME = "@ll_SANKI_II"
GROUP_LINK = "https://t.me/+QPSshOWJThczMWU1"

# 🔹 Welcome GIF & Inline Button
WELCOME_GIF = "https://firebasestorage.googleapis.com/v0/b/social-bite-skofficial.appspot.com/o/SANKI%2FBlack%20and%20Orange%20Modern%20Welcome%20to%20My%20Channel%20Video.mp4?alt=media&token=8971920d-151c-4a38-8fe0-8b1d3303eb65"  # ⚠️ Apni GIF ka link yahan daalo
SANKI_LINK = "https://t.me/AboutSanki"
GROUP_CHAT_ID = -1002590971976
# 🔹 Abuse Words List (Hindi + English + Short Forms)
ABUSE_WORDS = [
    "bc", "bkl", "mc", "mkc", "chutiya", "chutiyapa", "bsdk", "madarchod", "behenchod",
    "bhosdike", "gand", "gaand", "lodu", "loda", "lulli", "launde", "randi", "raand",
    "tatte", "tatti", "hijra", "kutta", "kamina", "kuttiya", "jhant", "chut", "chodu",
    "lund", "lunn", "gandu", "bitch", "fuck", "shit", "asshole", "dick", "pussy",
    "motherfucker", "bastard", "slut", "whore", "cock", "cunt", "retard", "suck",
    "scum", "faggot", "gaylord", "hoe", "nigga", "niga", "nigger", "boobs", "porn",
    "sexy", "sexx", "69", "horny", "dildo", "masturbate", "condom", "rape", "screw",
    "humping", "xxx", "nudes", "bra", "panty", "threesome", "orgy", "bdsm",
    "s3x", "p0rn", "xnx", "xvideos", "brazzers", "pornhub", "onlyfans", "ofans",
    "d1ck", "d!ck", "pu$$y", "pussi", "p0rnhub", "fuk", "fuc", "fack", "b1tch",
    "b!tch", "s!ut", "f4ck", "fook", "c0ck", "n!gga", "n1gga", "d0g", "h0rny",
    "m0therfucker", "m@dar", "b@stard", "sh!t", "a$$", "b00bs", "phuck", "phuc"
]

# ✅ 500 Funny Replies List
FUNNY_REPLIES = [
    "Bhai, tu sach bol raha hai ya sapne dekh raha hai? 😂",
    "Haan haan, bilkul sahi baat! (Jo bhi tune bola wo samajh nahi aaya) 🤣",
    "Aree bhai, thoda relax ho ja, kahin dimag fry na ho jaye! 😆",
    "Teri baatein sunke ChatGPT bhi confuse ho gaya! 😂",
    "Agar logic dhoondhne nikla na, to NASA wale tujhe utha le jayenge! 🤯",
    "Haan bhai, ab bas ek Nobel Prize bhi le aa! 🤣",
    "Teri baatein sunke lagta hai mujhe bhi tuition lena padega! 📚😵",
    "Kuch bhi ho bhai, tu asli legend hai! 😂🔥",
    "Bas bhai, zyada mat uda, hawa me ur jayega! ✈️😂",
    "Tu kya apni autobiography likh raha hai yaha? 📖🤣",
    "Bhai tu kya soch raha hai, bata sabko bhi! 😆",
    "Lagta hai Google se direct download maar raha hai! 🤣",
    "Bhai, agar yeh joke tha to mujhe ab rona aa raha hai! 😭😂",
    "Tere level ka dimag chahiye mujhe bhi! 🤯",
    "Bhai, tujhe award milega ‘Bakchodi King’ ka! 👑😂",
    "Lagta hai beta Elon Musk ka secret assistant hai! 🤣",
    "Bhagwaan ke diya gyan ko accept kar! 😂",
    "Bhai, teri baat likh ke rakhta hoon, future me use aayegi! 🤣",
    "Kya talent hai bhai! Bollywood se call aayega abhi! 🎭😂",
    "Mujhe bhi sikha bhai, tu kaise karta hai yeh sab? 🤣",
    "NASA wale bhi tujhe dhoondh rahe hain bhai! 🚀😂",
    "Bhai, tu pakka kisi doosre planet se aaya hai! 👽😂",
    "Bhai, teri soch limit cross kar chuki hai! 🔥😂",
    "Tu motivation speaker ban ja bhai! 🤣",
    "Bhai, mujhe bhi teri jaisi dimag chahiye! 🤯😂",
    "Koi ise award do, isne aaj history bana di! 🏆🤣",
    "Aree bhai, thoda chill kar, tension mat le! 🍹😂",
    "Bhai, tu toh kuch alag hi level ka banda hai! 🤣",
    "Tere jokes ke liye alag se dictionary likhni padegi! 📖😂",
    "Bhai, kya mast logic diya hai! 🔥😂",
    "Tu toh motivational speaker ban sakta hai! 🎤😂",
    "Ye baat sunke MUNNA BHAI bhi shock ho gaya hoga! 😆",
    "Aise logon ke wajah se WhatsApp band hone wala hai! 🤣",
    "Bhai, tu toh asli genius hai! 🔥😂",
    "Teri baat sunke mere dimaag ka fuse ud gaya! 💡💥😂",
    "Ek din history books me tera naam likha jayega! 📚😂",
    "Bhai, tu toh soch se bhi aage nikal gaya! 🚀😂",
    "Lagta hai tu hidden scientist hai! 🤯😂",
    "Aise hi baat karta raha, duniya tujhe yaad rakhegi! 🌍😂",
    "Bhai, tu toh Google se bhi fast hai! 🏎️😂",
    "Aapka dimaag kis factory me bana hai? 🤖😂",
    "Ye baat sunke WhatsApp ke server down ho gaye! 🤣",
    "Bhai, teri baat likh ke rakhta hoon future ke liye! 📜😂",
    "Tu asli legend hai bhai! 🔥😂",
    "Bhai, tere jaise log history banate hain! 📖😂",
    "Tere jokes ko bhi Oscar milna chahiye! 🏆😂",
    "Bhai, tu toh hamesha kuch alag hi kar raha hota hai! 🤣",
    "Teri baat sunke mera dimaag 360° ghoom gaya! 🔄😂",
    "Bhai, mujhe bhi apne dimaag ka backup bhej! 💾😂",
    "Lagta hai tu secret agent hai! 🕵️‍♂️😂",
    "Bhai, tujhe dekh ke lagta hai life easy hai! 😆",
    "Bhai, tera dimaag NASA wale udhar maang rahe hain! 🚀😂",
    "Tu aisa logic kaha se dhoondta hai bhai? 🧐😂",
    "Bhai, tu toh asli philosopher hai! 🎓😂",
    "Bhai, tu comedy king hai! 👑😂",
    "Kya baat hai bhai, tu toh Twitter se bhi tez hai! 🐦😂",
    "Bhai, tere jokes sunke main serious ho gaya! 🤨😂",
    "Bhai, tu toh asli meme lord hai! 🤣",
    "Teri baat sunke mera dimaag hang ho gaya! 💻😂",
    "Bhai, kya talent hai, abhi Hollywood se call aayega! 🎬😂",
    "Bhai, tere logic ko alag se samjhna padega! 🧠😂",
    "Tera dimaag supercomputer se tez hai bhai! 🖥️😂",
    "Bhai, tu toh aaj ka Einstein hai! 🔬😂",
    "Lagta hai tu future se aaya hai bhai! ⏳😂",
    "Tere baat sunke mere dimaag ki RAM full ho gayi! 🧠💾😂",
    "Bhai, tujhe alag se ek trophy milni chahiye! 🏆😂",
    "Ye baat sunke mera dimaag 404 error de raha hai! 🚫😂",
    "Tere jokes pe alag se copyright hona chahiye! 🎭😂",
    "Bhai, tu toh asli mastermind hai! 🧠😂",
]
