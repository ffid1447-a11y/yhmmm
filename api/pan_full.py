from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

RAZORPAY_URL = "https://razorpay.com/gst-number-search/pan/"
GST_INFO_API = "https://gstlookup.hideme.eu.org/?gstNumber="


@app.route("/pan", methods=["GET"])
def pan_lookup():
    pan = request.args.get("pan", "").strip()
    if not pan:
        return jsonify({"error": "Missing ?pan="}), 400

    url = f"{RAZORPAY_URL}{pan}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10) Chrome/142 Mobile Safari",
        "Accept": "*/*",
        "Referer": url
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return jsonify({"error": "Razorpay returned status " + str(r.status_code)}), 400

        soup = BeautifulSoup(r.text, "html.parser")

        # Extract candidate 15-char GST-like tokens
        gst_set = set()
        for text in soup.stripped_strings:
            t = text.strip()
            if len(t) == 15 and t.isalnum():
                gst_set.add(t.upper())

        gst_list = sorted(gst_set)

        details = []
        for gst in gst_list:
            try:
                rr = requests.get(GST_INFO_API + gst, timeout=12)
                # some endpoints return HTML or JSON; try JSON first
                data = rr.json() if 'application/json' in rr.headers.get('Content-Type', '') else rr.text
                details.append({"gst_number": gst, "info": data})
            except Exception:
                details.append({"gst_number": gst, "info": "Failed to fetch details"})

        return jsonify({
            "success": True,
            "pan": pan,
            "total_gst_found": len(gst_list),
            "gst_numbers": gst_list,
            "details": details
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500