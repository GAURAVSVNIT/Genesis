"use client";

import { useState } from "react";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState("");

  async function generate() {
    const res = await fetch("/api/generate", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    });
    const data = await res.json();
    setResult(data.blog);
  }

  return (
    <div className="p-10 max-w-3xl mx-auto">
      <textarea
        className="w-full border p-3"
        placeholder="Write a blog about..."
        onChange={(e) => setPrompt(e.target.value)}
      />
      <button onClick={generate} className="mt-4 px-4 py-2 bg-black text-white">
        Generate Blog
      </button>
      <pre className="mt-6 whitespace-pre-wrap">{result}</pre>
    </div>
  );
}
