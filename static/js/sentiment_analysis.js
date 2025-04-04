class SentimentAnalyzer {
    constructor() {
        // Confidence markers (positive and negative)
        this.confidenceMarkers = {
            positive: [
                "confident",
                "certainly",
                "definitely",
                "absolutely",
                "surely",
                "undoubtedly",
                "clearly",
                "obviously",
                "precisely",
                "exactly",
                "i know",
                "i am sure",
                "without doubt",
                "i believe",
                "i am confident",
                "i am certain",
            ],
            negative: [
                "maybe",
                "perhaps",
                "possibly",
                "probably",
                "somewhat",
                "i think",
                "i guess",
                "kind of",
                "sort of",
                "might",
                "i suppose",
                "i assume",
                "not sure",
                "uncertain",
                "unsure",
                "hopefully",
                "seems like",
                "in my opinion",
                "if i recall",
            ],
        };

        // Common filler words
        this.fillerWords = new Set([
            "um",
            "uh",
            "er",
            "ah",
            "like",
            "actually",
            "basically",
            "literally",
            "you know",
            "i mean",
            "sort of",
            "kind of",
            "so",
            "just",
            "well",
            "anyway",
            "right",
        ]);

        // Sentiment word lists (simplified)
        this.positiveWords = new Set([
            "good",
            "great",
            "excellent",
            "positive",
            "happy",
            "joyful",
            "success",
            "achieve",
            "win",
            "perfect",
            "best",
            "awesome",
            "fantastic",
            "wonderful",
            "amazing",
            "superb",
            "outstanding",
        ]);

        this.negativeWords = new Set([
            "bad",
            "poor",
            "negative",
            "unhappy",
            "sad",
            "angry",
            "failure",
            "lose",
            "worst",
            "terrible",
            "awful",
            "horrible",
            "disappointing",
            "frustrating",
            "problem",
            "issue",
            "difficult",
        ]);
    }

    cleanText(text) {
        if (!text) return "";

        // Convert to lowercase
        text = text.toLowerCase();

        // Remove URLs
        text = text.replace(/http\S+|www\S+|https\S+/g, "");

        // Remove mentions and hashtags
        text = text.replace(/@\w+|#\w+/g, "");

        // Remove punctuation
        text = text.replace(/[^\w\s]/g, "");

        // Remove extra whitespace
        text = text.replace(/\s+/g, " ").trim();

        return text;
    }

    tokenize(text) {
        return text.split(/\s+/);
    }

    analyzeSentiment(text) {
        const cleanedText = this.cleanText(text);
        const tokens = this.tokenize(cleanedText);

        let positiveCount = 0;
        let negativeCount = 0;
        let neutralCount = 0;

        for (const word of tokens) {
            if (this.positiveWords.has(word)) {
                positiveCount++;
            } else if (this.negativeWords.has(word)) {
                negativeCount++;
            } else {
                neutralCount++;
            }
        }

        const total = tokens.length || 1;
        const positive = positiveCount / total;
        const negative = negativeCount / total;
        const neutral = neutralCount / total;

        // Compound score (-1 to 1)
        const compound = (positiveCount - negativeCount) / total;

        return {
            positive,
            negative,
            neutral,
            compound,
        };
    }

    analyzeConfidence(text) {
        const textLower = text.toLowerCase();
        let positiveCount = 0;
        let negativeCount = 0;

        // Count positive and negative confidence markers
        for (const marker of this.confidenceMarkers.positive) {
            if (new RegExp(`\\b${marker}\\b`).test(textLower)) {
                positiveCount++;
            }
        }

        for (const marker of this.confidenceMarkers.negative) {
            if (new RegExp(`\\b${marker}\\b`).test(textLower)) {
                negativeCount++;
            }
        }

        // Word count for normalization
        const wordCount = this.tokenize(text).length;

        if (wordCount === 0) {
            return 50; // Neutral score for empty text
        }

        // Calculate confidence score (0-100)
        let confidenceScore = 50; // Base score
        confidenceScore += Math.min(
            40,
            (positiveCount / (wordCount / 100)) * 10
        );
        confidenceScore -= Math.min(
            40,
            (negativeCount / (wordCount / 100)) * 10
        );

        return Math.max(0, Math.min(100, confidenceScore));
    }

    analyzeClarity(text) {
        const sentences = text.split(/[.!?]+/).filter((s) => s.trim());
        const words = this.tokenize(this.cleanText(text));

        // Count filler words
        let fillerCount = 0;
        for (const word of words) {
            if (this.fillerWords.has(word)) {
                fillerCount++;
            }
        }

        const wordCount = words.length;
        const fillerRatio = wordCount > 0 ? fillerCount / wordCount : 0;

        // Calculate average sentence length
        let avgSentenceLength = 0;
        if (sentences.length > 0) {
            const lengths = sentences.map((s) => this.tokenize(s).length);
            avgSentenceLength =
                lengths.reduce((a, b) => a + b, 0) / lengths.length;
        }

        // Calculate vocabulary richness (type-token ratio)
        const uniqueWords = new Set(words.filter((w) => w.length > 2));
        const vocabularyRichness =
            wordCount > 0 ? uniqueWords.size / wordCount : 0;

        // Normalize metrics to 0-100 scale
        const normalizedFiller = Math.max(0, 100 - fillerRatio * 100 * 5);

        let normalizedSentenceLength;
        if (avgSentenceLength < 5) {
            normalizedSentenceLength = avgSentenceLength * 10;
        } else if (avgSentenceLength > 30) {
            normalizedSentenceLength = Math.max(
                0,
                100 - (avgSentenceLength - 30) * 3
            );
        } else {
            normalizedSentenceLength =
                100 - Math.abs(20 - avgSentenceLength) * 2;
        }

        let normalizedVocabulary;
        if (vocabularyRichness < 0.3) {
            normalizedVocabulary = vocabularyRichness * 100 * 2;
        } else if (vocabularyRichness > 0.9) {
            normalizedVocabulary = 100 - (vocabularyRichness - 0.9) * 100;
        } else {
            normalizedVocabulary = 60 + vocabularyRichness * 50;
        }

        // Combined clarity score
        const clarityScore =
            (normalizedFiller +
                normalizedSentenceLength +
                normalizedVocabulary) /
            3;

        return {
            score: Math.max(0, Math.min(100, clarityScore)),
            fillerRatio,
            avgSentenceLength,
            vocabularyRichness,
        };
    }

    analyzeText(text) {
        if (!text) {
            return {
                sentiment: {
                    positive: 0,
                    negative: 0,
                    neutral: 1,
                    compound: 0,
                },
                confidence: 0,
                clarity: 0,
                fillerRatio: 0,
                avgSentenceLength: 0,
                vocabularyRichness: 0,
            };
        }

        const sentiment = this.analyzeSentiment(text);
        const confidence = this.analyzeConfidence(text);
        const clarity = this.analyzeClarity(text);

        return {
            sentiment,
            confidence,
            clarity: clarity.score,
            fillerRatio: clarity.fillerRatio,
            avgSentenceLength: clarity.avgSentenceLength,
            vocabularyRichness: clarity.vocabularyRichness,
        };
    }
}

// Export for use in other files
if (typeof module !== "undefined" && module.exports) {
    module.exports = SentimentAnalyzer;
}
