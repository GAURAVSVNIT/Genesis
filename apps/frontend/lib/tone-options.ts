/**
 * Tone and Content Style Options
 * Provides configuration for different content generation tones and analysis options
 */

export const TONE_OPTIONS = {
  analytical: {
    label: "Analytical",
    description: "Critical analysis with multiple perspectives and nuanced discussion",
    icon: "🔬",
    ideal_for: "Deep dives, research, complex topics"
  },
  opinionated: {
    label: "Opinionated",
    description: "Strong viewpoints backed by evidence and reasoning",
    icon: "💡",
    ideal_for: "Opinion pieces, commentary, thought leadership"
  },
  critical: {
    label: "Critical",
    description: "Rigorous evaluation of ideas with strengths and weaknesses",
    icon: "⚖️",
    ideal_for: "Reviews, analysis, critiques"
  },
  investigative: {
    label: "Investigative",
    description: "Deep investigation uncovering hidden layers and patterns",
    icon: "🔍",
    ideal_for: "Exposés, in-depth reporting, pattern analysis"
  },
  contrarian: {
    label: "Contrarian",
    description: "Thoughtful challenges to conventional wisdom",
    icon: "💭",
    ideal_for: "Counter-narratives, alternative perspectives"
  }
}

export const ANALYSIS_OPTIONS = {
  include_critique: {
    label: "Include Critical Analysis",
    description: "Add critique section identifying weaknesses and limitations",
    default: true
  },
  include_alternatives: {
    label: "Include Alternative Perspectives",
    description: "Include opposing viewpoints and counterarguments",
    default: true
  },
  include_implications: {
    label: "Include Real-World Implications",
    description: "Explore consequences, winners, and losers",
    default: true
  }
}

export const TONE_DESCRIPTIONS: Record<string, string> = {
  analytical: "Presents multiple perspectives with critical examination of assumptions",
  opinionated: "Takes clear positions while respecting counterarguments",
  critical: "Identifies both strengths and significant weaknesses",
  investigative: "Digs beneath surface narratives and reveals hidden patterns",
  contrarian: "Challenges consensus views with evidence and reasoning"
}

export const TONE_EMOJIS: Record<string, string> = {
  analytical: "🔬",
  opinionated: "💡",
  critical: "⚖️",
  investigative: "🔍",
  contrarian: "💭"
}

export interface GenerationOptions {
  tone: keyof typeof TONE_OPTIONS
  include_critique: boolean
  include_alternatives: boolean
  include_implications: boolean
  length?: 'short' | 'medium' | 'long'
}

export const DEFAULT_OPTIONS: GenerationOptions = {
  tone: 'analytical',
  include_critique: true,
  include_alternatives: true,
  include_implications: true,
  length: 'medium'
}

/**
 * Get recommendations based on content type
 */
export function getRecommendationsForContentType(contentType: string): Partial<GenerationOptions> {
  const recommendations: Record<string, Partial<GenerationOptions>> = {
    'opinion-piece': {
      tone: 'opinionated',
      include_critique: true,
      include_alternatives: true
    },
    'analysis': {
      tone: 'analytical',
      include_critique: true,
      include_alternatives: true,
      include_implications: true
    },
    'review': {
      tone: 'critical',
      include_critique: true,
      include_alternatives: false
    },
    'investigation': {
      tone: 'investigative',
      include_critique: true,
      include_alternatives: true,
      include_implications: true
    },
    'counterargument': {
      tone: 'contrarian',
      include_critique: true,
      include_alternatives: true
    },
    'news': {
      tone: 'analytical',
      include_critique: false,
      include_alternatives: true
    }
  }
  
  return recommendations[contentType] || DEFAULT_OPTIONS
}
