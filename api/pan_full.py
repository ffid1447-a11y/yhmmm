from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

RAZORPAY_URL = "https://razorpay.com/gst-number-search/pan/"
GST_INFO_API = "https://gstlookup.hideme.eu.org/?gstNumber="


@app.route("/pan", methods=["GET"])
def pan_lookup():
    pan = request.args.get("pan")
    if not pan:
        return jsonify({"error": "Missing ?pan="}), 400

    try:
        # Step 1: Fetch Razorpay PAN page
        url = f"{RAZORPAY_URL}{pan}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10) Chrome/142 Mobile Safari",
            "Accept": "*/*",
            "Referer": url
        }

        razor = requests.get(url, headers=headers)
        if razor.status_code != 200:
            return jsonify({"error": "Razorpay blocked or PAN invalid"}), 400

        soup = BeautifulSoup(razor.text, "html.parser")

        # Step 2: Extract GST numbers
        gst_list = []
        possible = soup.find_all("div")
        for div in possible:
            text = div.get_text(strip=True)
            if len(text) == 15 and text.isalnum():
                gst_list.append(text)

        gst_list = list(set(gst_list))  # remove duplicates

        # Step 3: Fetch details for each GST number
        gst_details = []
        for gst in gst_list:
            try:
                r = requests.get(GST_INFO_API + gst, timeout=10)
                data = r.json()
                gst_details.append({
                    "gst_number": gst,
                    "info": data
                })
            except:
                gst_details.append({
                    "gst_number": gst,
                    "info": "Failed to fetch details"
                })

        # Final Response
        return jsonify({
            "success": True,
            "pan": pan,
            "total_gst_found": len(gst_list),
            "gst_numbers": gst_list,
            "details": gst_details
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# For Vercel (optional)
def handler(request, response):
    with app.test_request_context(
        path=request.path,
        method=request.method,
        query_string=request.query_string
    ):
        return app.full_dispatch_request()
