import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const audioFile = formData.get('audio');
    
    if (!audioFile) {
        return NextResponse.json(
            { error: 'No audio file provided' },
            { status: 400 }
        );
    }

    const apiKey = process.env.ELEVENLABS_API_KEY;

    if (!apiKey) {
      return NextResponse.json(
        { error: 'Server configuration error: Missing API Key' },
        { status: 500 }
      );
    }

    const elevenLabsFormData = new FormData();
    elevenLabsFormData.append('file', audioFile);
    elevenLabsFormData.append('model_id', 'scribe_v1');

    const response = await fetch('https://api.elevenlabs.io/v1/speech-to-text', {
      method: 'POST',
      headers: {
        'xi-api-key': apiKey,
      },
      body: elevenLabsFormData,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('ElevenLabs API Error:', response.status, errorData);
        return NextResponse.json(
            { error: `ElevenLabs API error: ${response.statusText}`, details: errorData },
            { status: response.status }
        );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Error processing speech-to-text request:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
