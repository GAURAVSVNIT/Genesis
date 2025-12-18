"""
Text chunking utilities for splitting large messages into embeddings.
Supports overlap for context preservation (like ChatGPT RAG).
"""

from typing import List, Tuple
import re


class TextChunker:
    """Split text into chunks for embedding (ChatGPT-style)."""
    
    def __init__(
        self,
        chunk_size: int = 512,  # Characters per chunk
        overlap: int = 50,  # Character overlap between chunks
        separator: str = "\n\n"  # Primary separator (paragraphs)
    ):
        """
        Initialize text chunker.
        
        Args:
            chunk_size: Target characters per chunk
            overlap: Overlap between chunks for context
            separator: Primary separator (try to split here first)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separator = separator

    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if not text or len(text) <= self.chunk_size:
            return [text]
        
        # Try to split by separator first (preserves context)
        separators = [
            "\n\n",      # Paragraph break
            "\n",        # Line break
            ". ",        # Sentence
            " ",         # Word
            ""           # Character
        ]
        
        good_splits = []
        separator = self.separator
        
        for _s in separators:
            if _s == "":
                separator = _s
                break
            if _s in text:
                separator = _s
                break
        
        # Split by separator
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)
        
        # Merge splits into chunks
        good_splits = [s for s in splits if s]
        merged_text = []
        current_chunk = ""
        
        for split in good_splits:
            test_chunk = current_chunk + separator + split if current_chunk else split
            
            if len(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    merged_text.append(current_chunk)
                current_chunk = split
        
        if current_chunk:
            merged_text.append(current_chunk)
        
        # Create chunks with overlap
        chunks = []
        for i in range(len(merged_text)):
            chunk = merged_text[i]
            
            # Add overlap from previous chunk
            if i > 0 and self.overlap > 0:
                prev_chunk = merged_text[i - 1]
                if len(prev_chunk) > self.overlap:
                    overlap_text = prev_chunk[-self.overlap:]
                    chunk = overlap_text + chunk
            
            chunks.append(chunk)
        
        return chunks

    def split_with_metadata(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Split text into chunks with position metadata.
        
        Args:
            text: Text to split
            
        Returns:
            List of (chunk_text, start_char, end_char) tuples
        """
        chunks = self.split_text(text)
        chunks_with_pos = []
        
        current_pos = 0
        for chunk in chunks:
            # Find chunk position in original text (accounting for overlap)
            start_pos = text.find(chunk[0:min(50, len(chunk))], current_pos)
            if start_pos == -1:
                start_pos = current_pos
            
            end_pos = start_pos + len(chunk)
            chunks_with_pos.append((chunk, start_pos, end_pos))
            current_pos = end_pos - self.overlap
        
        return chunks_with_pos

    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimate of token count (1 token ≈ 4 characters).
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        return len(text) // 4

    def get_chunk_stats(self, text: str) -> dict:
        """
        Get statistics about text chunking.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with chunk statistics
        """
        chunks = self.split_text(text)
        return {
            "total_length": len(text),
            "total_tokens": self.estimate_tokens(text),
            "num_chunks": len(chunks),
            "avg_chunk_length": len(text) // len(chunks) if chunks else 0,
            "max_chunk_length": max(len(c) for c in chunks) if chunks else 0,
            "min_chunk_length": min(len(c) for c in chunks) if chunks else 0,
        }


# Preset chunk configurations (like ChatGPT)
CHUNK_CONFIGS = {
    "small": {
        "chunk_size": 256,
        "overlap": 32,
        "separator": "\n\n"
    },
    "medium": {
        "chunk_size": 512,  # Default
        "overlap": 50,
        "separator": "\n\n"
    },
    "large": {
        "chunk_size": 1024,
        "overlap": 100,
        "separator": "\n\n"
    },
    "xlarge": {
        "chunk_size": 2048,
        "overlap": 200,
        "separator": "\n\n"
    }
}


def get_chunker(config: str = "medium") -> TextChunker:
    """
    Get a pre-configured text chunker.
    
    Args:
        config: 'small', 'medium', 'large', or 'xlarge'
        
    Returns:
        Configured TextChunker instance
    """
    if config not in CHUNK_CONFIGS:
        config = "medium"
    
    cfg = CHUNK_CONFIGS[config]
    return TextChunker(**cfg)


# Example usage:
if __name__ == "__main__":
    text = """
    This is a long message that needs to be chunked.
    
    It contains multiple paragraphs and different sections.
    
    The chunking algorithm will split this text intelligently,
    preserving context with overlaps between chunks.
    
    This is useful for embedding large texts like blog posts or conversations.
    """
    
    chunker = get_chunker("medium")
    chunks = chunker.split_text(text)
    
    print(f"Original text length: {len(text)} chars")
    print(f"Number of chunks: {len(chunks)}")
    print("\nChunks:")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1} ({len(chunk)} chars):")
        print(f"  {chunk[:100]}...")
    
    stats = chunker.get_chunk_stats(text)
    print(f"\nStats: {stats}")
