# 🎯 Campus Connect: Smart & Secure Lost and Found

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Framework-Flask-black.svg?logo=flask)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**Campus Connect** is a centralized, AI-powered web application designed to modernize the Lost & Found experience on university campuses. It replaces chaotic WhatsApp groups and manual logbooks with a smart, location-aware, and highly secure platform.

---

## ✨ Key Features

* 🤖 **AI Visual Fingerprinting:** Uses Perceptual Hashing (`imagehash`) to analyze uploaded photos and automatically suggest matches between lost and found items.
* 🔐 **Secure "Digital Handshake" (OTP):** Prevents fraudulent claims. The finder receives a secret 4-digit PIN. The owner must enter this PIN in their app during the physical meetup to successfully claim the item.
* 📍 **Interactive Geolocation:** Integrated with **Leaflet.js**. Users can auto-locate via GPS or manually drop a pin on the campus map to show exactly where an item was lost or found.
* 🏆 **Gamification (Karma Points):** Encourages good campus citizenship. Users earn "+20 Karma" for successfully returning items to their rightful owners.
* 🧹 **Smart Feed Auto-Cleanup:** Once an item is claimed via the secure PIN, both the "Found" report and the corresponding "Lost" report are automatically resolved and removed from the active feed.
* 📱 **PWA Ready:** Fully responsive UI built with Bootstrap 5, complete with a web manifest for a native mobile app feel.

---

## 🛠️ Tech Stack

**Backend:** Python, Flask, SQLAlchemy, Werkzeug Security  
**Database:** SQLite  
**Frontend:** HTML5, Jinja2, Bootstrap 5, CSS3  
**APIs & Libraries:** Leaflet.js (Maps), OpenStreetMap, Pillow, ImageHash  

---

## 🚀 How It Works (The Handover Protocol)

1.  **Report:** Student A finds a wallet, snaps a photo, drops a pin on the map, and submits.
2.  **Match:** AI scans existing "Lost" reports for visual and textual similarities.
3.  **Secure Handover:** Student A receives a **Handover PIN** (e.g., `4829`).
4.  **Claim:** Student A and Student B (the owner) meet. Student B logs in, clicks "Claim", and enters `4829`.
5.  **Resolve:** The system verifies the PIN, marks the item as returned, closes Student B's lost report, and awards Student A with Karma points!

---

## 💻 Installation & Local Setup

To run this project locally on your machine, follow these steps:

### 1. Clone the repository
```bash
git clone [https://github.com/CodeBlooded-69/Lost-Found.git](https://github.com/CodeBlooded-69/Lost-Found.git)
cd campus-connect
