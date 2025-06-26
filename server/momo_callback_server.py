from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/momo/callback", methods=["POST"])
def momo_callback():
    data = request.json
    print("Callback received:", data)
    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    app.run(port=5000)

