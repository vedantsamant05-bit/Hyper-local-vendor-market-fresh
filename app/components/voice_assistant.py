import streamlit as st
import streamlit.components.v1 as components
import json

def render_voice_assistant(products_list, lang="English"):
    # Generate the text to read aloud for TTS
    tts_parts = []
    for p in products_list:
        p_name = p["name"]
        p_price = st.session_state.inventory.get(p_name, {"price": p.get("price", 0)})["price"]
        tts_parts.append(f"{p_name} is {p_price} rupees per {p['unit']}")
    tts_text = ", ".join(tts_parts)

    # Dictionary of UI text for the assistant frame
    ui_texts = {
        "English": {
            "title": "Voice Pricing Assistant",
            "listen": "🎙️ Listen",
            "listening": "🎤 Listening...",
            "speak": "🔊 Speak Inventory",
            "help": "Speak: '[Vegetable Name] [Price]'. E.g. 'Tomatoes forty five'",
            "status_idle": "Ready for voice command",
            "status_error": "Could not recognize. Try again.",
            "status_success": "Updating {prod} to ₹{price}..."
        },
        "Hindi": {
            "title": "आवाज़ सहायता",
            "listen": "🎙️ बोलना शुरू करें",
            "listening": "🎤 सुन रहा है...",
            "speak": "🔊 इन्वेंटरी पढ़ें",
            "help": "बोलें: '[सब्जी का नाम] [कीमत]'। जैसे: 'टमाटर पैंतालीस'",
            "status_idle": "वॉयस कमांड के लिए तैयार",
            "status_error": "पहचान नहीं पाया। फिर कोशिश करें।",
            "status_success": "{prod} को ₹{price} पर अपडेट कर रहा है..."
        },
        "Marathi": {
            "title": "आवाज सहाय्यक",
            "listen": "🎙️ बोला",
            "listening": "🎤 ऐकत आहे...",
            "speak": "🔊 इन्व्हेंटरी वाचा",
            "help": "बोला: '[भाजीचे नाव] [किंमत]'. उदा: 'टोमॅटो पंचेचाळीस'",
            "status_idle": "व्हॉइस कमांडसाठी तयार",
            "status_error": "ओळखता आले नाही. पुन्हा प्रयत्न करा.",
            "status_success": "{prod} ₹{price} वर अपडेट करत आहे..."
        }
    }
    
    t = ui_texts.get(lang, ui_texts["English"])
    
    # HTML component with JS Web Speech API
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'DM Sans', sans-serif;
                margin: 0;
                padding: 10px;
                background: linear-gradient(135deg, #ffffffef, #ffffffbb);
                color: #173826;
                border-radius: 16px;
            }}
            .container {{
                display: flex;
                flex-direction: column;
                gap: 8px;
            }}
            .header {{
                font-size: 0.95rem;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .buttons {{
                display: flex;
                gap: 8px;
            }}
            .btn {{
                padding: 6px 12px;
                border-radius: 8px;
                border: 1px solid #159c6522;
                background: linear-gradient(135deg, #36c983, #159c65);
                color: white;
                font-weight: bold;
                font-size: 0.8rem;
                cursor: pointer;
                transition: transform 0.1s;
                display: flex;
                align-items: center;
                gap: 4px;
            }}
            .btn:active {{
                transform: scale(0.97);
            }}
            .btn-secondary {{
                background: linear-gradient(135deg, #ff8f66, #d85726);
            }}
            .status {{
                font-size: 0.78rem;
                color: #557063;
                background: #f1f5f3;
                padding: 6px 10px;
                border-radius: 6px;
                border-left: 3px solid #159c65;
            }}
            .help-text {{
                font-size: 0.72rem;
                color: #777;
                font-style: italic;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <span>{t['title']}</span>
                <span class="help-text">{t['help']}</span>
            </div>
            <div class="buttons">
                <button id="btn-listen" class="btn" onclick="startDictation()">{t['listen']}</button>
                <button id="btn-speak" class="btn btn-secondary" onclick="speakInventory()">{t['speak']}</button>
            </div>
            <div id="status-box" class="status">
                {t['status_idle']}
            </div>
        </div>

        <script>
            const textToSpeak = {json.dumps(tts_text)};
            const statusBox = document.getElementById('status-box');
            const listenBtn = document.getElementById('btn-listen');
            
            function speakInventory() {{
                if ('speechSynthesis' in window) {{
                    window.speechSynthesis.cancel();
                    const utterance = new SpeechSynthesisUtterance(textToSpeak);
                    
                    // Set language dialect based on selection
                    const lang = "{lang}";
                    if (lang === "Hindi") utterance.lang = 'hi-IN';
                    else if (lang === "Marathi") utterance.lang = 'mr-IN';
                    else utterance.lang = 'en-IN';
                    
                    window.speechSynthesis.speak(utterance);
                }} else {{
                    alert("Text-to-Speech is not supported in this browser.");
                }}
            }}

            // Product keywords mapping
            const prodMap = [
                {{ id: "Farm Fresh Tomatoes", keywords: ["tomato", "tomatoes", "tomat", "टमाटर", "टोमॅटो"] }},
                {{ id: "Spinach Bunch", keywords: ["spinach", "spinach bunch", "palak", "पालक"] }},
                {{ id: "Baby Potatoes", keywords: ["potato", "potatoes", "aaloo", "aloo", "batata", "आलू", "बटाटा", "बटाटे"] }},
                {{ id: "Tender Okra", keywords: ["okra", "lady finger", "ladyfinger", "bhindi", "bhendi", "भिंडी", "भेंडी"] }},
                {{ id: "Rainbow Carrots", keywords: ["carrot", "carrots", "gajar", "गाजर"] }},
                {{ id: "Broccoli", keywords: ["broccoli", "ब्रोकोली", "ब्रोकोली"] }},
                {{ id: "Bottle Gourd", keywords: ["bottle gourd", "gourd", "lauki", "dudhi", "दूधी", "भोपळा"] }},
                {{ id: "Red Bell Pepper", keywords: ["bell pepper", "pepper", "peppers", "capsicum", "shimla", "ढोबळी मिरची", "ढोबळी", "शिमला"] }}
            ];

            // Hindi/Marathi spoken numbers word-to-digit mapper
            const numberWords = {{
                "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
                "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
                "एक": 1, "दोन": 2, "तीन": 3, "चार": 4, "पाच": 5, "सहा": 6, "सात": 7, "आठ": 8, "नऊ": 9, "दहा": 10,
                "वीस": 20, "तीस": 30, "चाळीस": 40, "पन्नास": 50, "साठ": 60, "सत्तर": 70, "ऐंशी": 80, "नव्वद": 90, "शंभर": 100,
                "दस": 10, "बीस": 20, "तीस": 30, "चालीस": 40, "पचास": 50, "साठ": 60, "सत्तर": 70, "अस्सी": 80, "नब्बे": 90, "सौ": 100,
                "पाच": 5, "पन्नास": 50
            }};

            function parseSpokenNumber(words) {{
                // Extract directly matching digits
                let match = words.match(/\\d+/);
                if (match) return parseInt(match[0]);

                let total = 0;
                let wordList = words.toLowerCase().split(/[\\s-]+/);
                
                // Try compiling text numbers like "forty five" or "तीस पाच" (thirty five)
                for (let word of wordList) {{
                    if (numberWords[word] !== undefined) {{
                        total += numberWords[word];
                    }}
                }}
                
                // Fallback: check if a combination of words maps to standard Indian numbers
                // E.g. "forty" + "five"
                if (total > 0) return total;
                return null;
            }}

            function startDictation() {{
                if (window.hasOwnProperty('webkitSpeechRecognition') || window.hasOwnProperty('SpeechRecognition')) {{
                    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    const recognition = new SpeechRecognition();

                    recognition.continuous = false;
                    recognition.interimResults = false;

                    const lang = "{lang}";
                    if (lang === "Hindi") recognition.lang = 'hi-IN';
                    else if (lang === "Marathi") recognition.lang = 'mr-IN';
                    else recognition.lang = 'en-IN';

                    recognition.onstart = function() {{
                        listenBtn.innerText = "{t['listening']}";
                        statusBox.innerText = "{t['listening']}";
                        statusBox.style.borderLeftColor = "#ff8f66";
                    }};

                    recognition.onresult = function(e) {{
                        recognition.stop();
                        const transcript = e.results[0][0].transcript.toLowerCase();
                        statusBox.innerText = `"${{transcript}}"`;
                        
                        // Parse command
                        let detectedProduct = null;
                        for (let prod of prodMap) {{
                            for (let kw of prod.keywords) {{
                                if (transcript.includes(kw)) {{
                                    detectedProduct = prod.id;
                                    break;
                                }}
                            }}
                            if (detectedProduct) break;
                        }}

                        let detectedPrice = parseSpokenNumber(transcript);

                        if (detectedProduct && detectedPrice) {{
                            let successMsg = "{t['status_success']}"
                                .replace("{{prod}}", detectedProduct)
                                .replace("{{price}}", detectedPrice);
                            statusBox.innerText = successMsg;
                            statusBox.style.borderLeftColor = "#36c983";
                            
                            // Send updates to query parameter of parent window
                            setTimeout(() => {{
                                const parentUrl = new URL(window.parent.location.href);
                                parentUrl.searchParams.set('update_prod', detectedProduct);
                                parentUrl.searchParams.set('update_price', detectedPrice);
                                window.parent.location.href = parentUrl.toString();
                            }}, 800);
                        }} else {{
                            statusBox.innerText = "{t['status_error']} (Got: " + transcript + ")";
                            statusBox.style.borderLeftColor = "#d85726";
                        }}
                    }};

                    recognition.onerror = function(e) {{
                        recognition.stop();
                        statusBox.innerText = "{t['status_error']} (Error: " + e.error + ")";
                        statusBox.style.borderLeftColor = "#d85726";
                        listenBtn.innerText = "{t['listen']}";
                    }};

                    recognition.onend = function() {{
                        listenBtn.innerText = "{t['listen']}";
                    }};

                    recognition.start();
                }} else {{
                    alert("Speech Recognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
                }}
            }}
        </script>
    </body>
    </html>
    """
    # Render component frame
    components.html(html_code, height=130, scrolling=False)
