#!/usr/bin/env python3
"""Make one Yasmin (ms-MY) voice line per scene, with word timings."""
import asyncio, json, os, sys
import ssl
import edge_tts
import edge_tts.communicate as _c
_c._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")  # session proxy CA

OUT = sys.argv[1]
VOICE = "ms-MY-YasminNeural"
RATE = "+5%"
LINES = {
    "hook": "Siapa kata nak memiliki emas, kena keluarkan modal besar, atau bayar harga mahal?",
    "kilang": "Di Umar Jewelleries, emas pada harga kilang, ikut keperluan dan kemampuan anda.",
    "goldbar": "Nak simpan emas? Gold Bar, sembilan sembilan sembilan perpuluhan sembilan.",
    "kemas": "Nak bergaya? Barang kemas sembilan satu enam, pelbagai design cantik.",
    "dinar": "Nak koleksi syiling? Dinar emas pun ada.",
    "soalan": "Tapi tahu tak, apa yang paling menarik tentang Umar Jewelleries?",
    "ekosistem": "Anda bukan sekadar beli emas. Anda juga berpeluang kenali ilmu emas, bina simpanan, dan jana pendapatan, melalui ekosistem dealer Umar Jewelleries.",
    "falsafah": "Bagi saya, emas bukan sekadar perhiasan, tapi usaha merancang kewangan masa depan.",
    "cta": "Jom kenali Umar Jewelleries! Cantik dipakai, bijak disimpan, peluang pendapatan jangan dilepaskan! Jom daftar dealer sekarang!",
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
