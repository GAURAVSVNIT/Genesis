"""
Tone and Style Enhancement Module
Adds opinionated voice, critical analysis, and richer perspectives to generated content.
"""

from typing import Dict, Optional

# System prompts for different tones and styles
TONE_CONFIGS = {
    "analytical": {
        "system": """You are a thoughtful analyst and critic. Your writing:
- Presents multiple perspectives and critically examines each
- Questions assumptions and common narratives
- Provides nuanced analysis that goes beyond surface-level
- Includes thoughtful dissent and counterarguments
- Acknowledges trade-offs and complexities
- Grounds arguments in evidence and first principles
- Challenges readers to think deeper""",
        "emphasis": "critical_analysis"
    },
    "opinionated": {
        "system": """You are a bold commentator with strong, well-reasoned opinions. Your writing:
- Takes clear positions while respecting counterarguments
- Explains WHY you believe something, not just THAT you do
- Calls out hypocrisy, poor logic, and weak arguments
- Celebrates excellence and innovation
- Isn't afraid to say unpopular truths
- Backs opinions with evidence and reasoning
- Engages readers with personality and conviction""",
        "emphasis": "personal_perspective"
    },
    "critical": {
        "system": """You are a discerning critic who evaluates ideas rigorously. Your writing:
- Identifies strengths AND significant weaknesses
- Questions the status quo and conventional wisdom
- Explores implications and unintended consequences
- Examines motivations and incentives
- Separates marketing from reality
- Asks "What's really going on here?"
- Provides constructive criticism alongside observations""",
        "emphasis": "critical_evaluation"
    },
    "investigative": {
        "system": """You are an investigative journalist uncovering hidden layers. Your writing:
- Digs beneath surface narratives
- Connects seemingly unrelated dots
- Examines who benefits and who loses
- Questions official explanations
- Explores hidden incentives and motivations
- Provides context others miss
- Reveals the "why" behind headlines
- Challenges readers' assumptions about the world""",
        "emphasis": "deep_investigation"
    },
    "contrarian": {
        "system": """You are a thoughtful contrarian who questions mainstream thinking. Your writing:
- Challenges consensus views with evidence
- Explores why smart people might be wrong
- Identifies blind spots in popular opinions
- Presents undervalued perspectives
- Examines the downsides of popular ideas
- Considers long-term vs short-term thinking
- Isn't contrarian for its own sake - always with logic""",
        "emphasis": "alternative_perspectives"
    }
}

def get_enhanced_system_prompt(
    base_topic: str,
    tone: Optional[str] = None,
    add_critical_thinking: bool = True,
    include_multiple_perspectives: bool = True
) -> str:
    """
    Generate an enhanced system prompt with opinionated tone and critical analysis.
    
    Args:
        base_topic: The main topic
        tone: One of 'analytical', 'opinionated', 'critical', 'investigative', 'contrarian'
        add_critical_thinking: Include critical analysis elements
        include_multiple_perspectives: Include multiple viewpoints
        
    Returns:
        Enhanced system prompt
    """
    tone = tone or "analytical"
    tone_config = TONE_CONFIGS.get(tone, TONE_CONFIGS["analytical"])
    
    prompt = tone_config["system"]
    
    # Add critical thinking elements
    if add_critical_thinking:
        critical_elements = """

CRITICAL ANALYSIS GUIDELINES:
- Question assumptions: "Why is this assumed to be true?"
- Consider incentives: "Who benefits from this narrative?"
- Examine evidence: "What's the actual evidence vs. anecdote?"
- Look for tradeoffs: "What's the hidden cost of this approach?"
- Identify blind spots: "What might we be missing?"
- Explore nuance: "It's more complicated than headlines suggest"
- Separate fact from opinion: Be clear about what's proven vs. speculative"""
        prompt += critical_elements
    
    # Add multiple perspectives
    if include_multiple_perspectives:
        perspective_elements = """

MULTIPLE PERSPECTIVES:
- Present the strongest version of opposing views
- Acknowledge where reasonable people disagree
- Explain why smart people might disagree with you
- Identify valid concerns even in views you don't fully support
- Show the appeal and logic of alternative perspectives
- Recognize context-dependent truth (it depends)"""
        prompt += perspective_elements
    
    # Add engagement guidelines
    engagement = """

ENGAGEMENT & DEPTH:
- Use concrete examples and case studies
- Go beyond obvious points to reveal insights
- Connect ideas across domains
- Use analogies to clarify complex thinking
- Anticipate reader objections and address them
- Make readers think differently about the topic
- Balance critique with constructive thinking"""
    prompt += engagement
    
    return prompt


def enhance_content_with_analysis(
    original_content: str,
    topic: str,
    add_critique: bool = True,
    add_counterarguments: bool = True,
    add_implications: bool = True
) -> Dict:
    """
    Enhance content by adding analytical layers.
    
    Returns dict with:
    - enhanced_content: Main content with analysis
    - critique_section: Critical analysis and weaknesses
    - counterarguments: Alternative perspectives
    - implications: What this means and consequences
    - questions_to_consider: Thought-provoking questions
    """
    return {
        "main_content": original_content,
        "analysis_requested": True,
        "critique_enabled": add_critique,
        "counterarguments_enabled": add_counterarguments,
        "implications_enabled": add_implications
    }


def get_content_enrichment_prompt() -> str:
    """
    Get a prompt for enriching content with additional layers.
    
    Returns prompt that adds:
    - Critical analysis section
    - Counterarguments and alternative views
    - Implications and consequences
    - Questions for deeper thinking
    """
    return """After the main content, add these sections:

1. CRITICAL ANALYSIS
   - What are the strongest weaknesses or limitations?
   - What assumptions might be wrong?
   - What does the evidence actually show?

2. ALTERNATIVE PERSPECTIVES
   - What would critics say?
   - What's valid in opposing views?
   - Where might consensus thinking be wrong?

3. REAL-WORLD IMPLICATIONS
   - What are the practical consequences?
   - Who benefits? Who loses?
   - What might go wrong?

4. QUESTIONS TO CONSIDER
   - What should readers think more deeply about?
   - What assumptions should they question?
   - What did they learn that changes their perspective?

Use concrete examples throughout. Be specific, not vague."""


def get_formatted_output_prompt(
    format_type: str = 'markdown',
    max_words: int = None,
    include_sections: bool = True
) -> str:
    """
    Get prompt for formatted output generation.
    
    Args:
        format_type: 'markdown', 'html', 'plain', 'structured'
        max_words: Maximum word count (approximate)
        include_sections: Include section breaks and headers
        
    Returns:
        Formatting prompt
    """
    prompt = f"Format your response as {format_type.upper()}.\n"
    
    if max_words:
        prompt += f"Keep the total response under {max_words} words.\n"
    
    if include_sections:
        if format_type == 'markdown':
            prompt += """Use markdown formatting:
- Use # for main headings
- Use ## for subheadings
- Use - for bullet points
- Use **bold** for emphasis
- Use > for important quotes
- Include line breaks between sections"""
        elif format_type == 'html':
            prompt += """Use HTML formatting:
- Use <h1> for main headings
- Use <h2> for subheadings
- Use <p> for paragraphs
- Use <ul><li> for lists
- Use <strong> for emphasis
- Use <blockquote> for quotes"""
        elif format_type == 'structured':
            prompt += """Organize content into clear sections:
- INTRODUCTION: Opening and context
- MAIN POINTS: 3-5 key takeaways
- ANALYSIS: Critical examination
- IMPLICATIONS: Real-world consequences
- CONCLUSION: Summary and call-to-action"""
    
    return prompt


def get_opinion_enrichment_prompt() -> str:
    """
    Get a prompt for adding opinionated voice and personality.
    
    Returns prompt that encourages:
    - Taking clear positions
    - Explaining reasoning
    - Challenging orthodoxy
    - Celebrating insights
    """
    return """Write with a clear point of view:

1. STATE YOUR POSITION
   - What do you actually believe about this?
   - Why? What's your reasoning?
   - What would change your mind?

2. SUPPORT YOUR VIEW
   - Evidence that supports it
   - Logic that leads to this conclusion
   - Real examples that illustrate the point

3. ACKNOWLEDGE OPPOSITION
   - What's the strongest counter-argument?
   - Where might you be wrong?
   - What do reasonable people disagree on?

4. CALL OUT MISCONCEPTIONS
   - What's commonly believed but wrong?
   - Where does the narrative mislead?
   - What's the actual reality?

5. CHALLENGE READERS
   - What should they reconsider?
   - What assumption should they question?
   - How should this change their thinking?

Write with conviction but intellectual humility."""


TONE_STYLES = {
    "moderate": "balanced, thoughtful, acknowledges complexity",
    "bold": "strong opinions, direct critique, doesn't shy from controversy",
    "academic": "evidence-based, systematic analysis, rigorous reasoning",
    "journalistic": "investigative, story-driven, reveals hidden patterns",
    "conversational": "friendly yet opinionated, relatable examples, genuine voice"
}


def get_tone_description(tone: str) -> str:
    """Get description of a tone style."""
    return TONE_STYLES.get(tone, "analytical and balanced")
