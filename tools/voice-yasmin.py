#!/usr/bin/env python3
"""Make one Yasmin (ms-MY) voice line per scene, with word timings."""
import asyncio, json, os, sys
import ssl
import edge_tts
import edge_tts.communicate as _c
_c._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")  # session proxy CA

OUT = sys.argv[1]
VOICE = "ms-MY-YasminNeural"
RATE = "+0%"
LINES = {
    "hook": "Siapa kata nak memiliki emas, kena keluarkan modal yang besar, atau bayar harga yang mahal?",
    "kilang": "Di Umar Jewelleries, kita bawakan emas dengan harga kilang, dan pelbagai pilihan mengikut keperluan serta kemampuan anda.",
    "goldbar": "Nak simpan emas? Kita ada Gold Bar, sembilan sembilan sembilan perpuluhan sembilan.",
    "kemas": "Nak emas untuk dipakai dan bergaya? Kita ada barang kemas sembilan satu enam, dengan pelbagai design yang cantik dan menarik.",
    "dinar": "Nak koleksi emas dalam bentuk syiling? Kita juga ada dinar emas.",
    "soalan": "Tapi, tahu tak apa yang paling menarik tentang Umar Jewelleries?",
    "peluang": "Kita bukan sekadar menawarkan pilihan emas pada harga kilang, malah kita juga membuka peluang kepada masyarakat untuk membina simpanan emas, dan meneroka peluang menjana pendapatan.",
    "ekosistem": "Maksudnya, anda bukan sekadar datang membeli emas untuk kegunaan sendiri, tetapi anda juga berpeluang mengenali ilmu emas, membina simpanan, dan menjana pendapatan, melalui ekosistem dealer Umar Jewelleries.",
    "falsafah": "Sebab bagi saya, emas bukan sekadar perhiasan. Emas juga boleh menjadi salah satu usaha kita merancang kewangan masa depan.",
    "cta": "Jom kenali Umar Jewelleries! Beli emas, bina simpanan, dan terokai peluang menjana pendapatan bersama kami. Cantik dipakai, bijak disimpan, peluang pendapatan jangan dilepaskan! Jom daftar dealer sekarang!",
}


async def one(key, text):
    com = edge_tts.Communicate(text, VOICE, rate=RATE, boundary="WordBoundary")
    words, audio = [], bytearray()
    async for ch in com.stream():
        if ch["type"] == "audio":
            audio += ch["data"]
        elif ch["type"] == "WordBoundary":
            words.append({"w": ch["text"], "t": round(ch["offset"] / 1e7, 3),
                          "d": round(ch["duration"] / 1e7, 3)})
    with open(os.path.join(OUT, f"{key}.mp3"), "wb") as f:
        f.write(audio)
    return key, words


async def main():
    os.makedirs(OUT, exist_ok=True)
    res = {}
    for k, t in LINES.items():
        key, words = await one(k, t)
        res[key] = words
    json.dump(res, open(os.path.join(OUT, "words.json"), "w"), indent=1)

asyncio.run(main())
