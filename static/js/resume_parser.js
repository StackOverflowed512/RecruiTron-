class ResumeParser {
    constructor() {
        // Common job titles and related keywords
        this.roleKeywords = {
            "Software Engineer": [
                "software engineer",
                "developer",
                "programmer",
                "coder",
                "software development",
                "web developer",
                "full stack",
                "backend",
                "frontend",
            ],
            "Data Scientist": [
                "data scientist",
                "data analyst",
                "machine learning",
                "deep learning",
                "AI",
                "artificial intelligence",
                "statistics",
                "analytics",
            ],
            "UX/UI Designer": [
                "ux",
                "ui",
                "user experience",
                "user interface",
                "designer",
                "graphic",
                "web design",
                "product design",
            ],
            "Product Manager": [
                "product manager",
                "product owner",
                "program manager",
                "scrum master",
                "agile",
                "sprint",
            ],
            "DevOps Engineer": [
                "devops",
                "cloud",
                "aws",
                "azure",
                "gcp",
                "kubernetes",
                "docker",
                "ci/cd",
                "jenkins",
            ],
            "Financial Analyst": [
                "financial",
                "finance",
                "accounting",
                "analyst",
                "investment",
                "banking",
                "portfolio",
            ],
            "HR Specialist": [
                "hr",
                "human resources",
                "recruiting",
                "talent",
                "acquisition",
                "hiring",
                "onboarding",
                "hr manager",
            ],
        };

        // Common technical skills
        this.techSkills = [
            "python",
            "java",
            "javascript",
            "c++",
            "c#",
            "ruby",
            "php",
            "swift",
            "kotlin",
            "go",
            "rust",
            "react",
            "angular",
            "vue",
            "node.js",
            "express",
            "django",
            "flask",
            "spring",
            "laravel",
            "asp.net",
            "sql",
            "mysql",
            "postgresql",
            "mongodb",
            "firebase",
            "oracle",
            "sql server",
            "redis",
            "cassandra",
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "terraform",
            "jenkins",
            "ci/cd",
            "git",
            "github",
            "tensorflow",
            "pytorch",
            "scikit-learn",
            "pandas",
            "numpy",
            "keras",
            "opencv",
            "nltk",
            "spacy",
            "html",
            "css",
            "sass",
            "bootstrap",
            "tailwind",
            "jquery",
            "webpack",
            "babel",
            "typescript",
            "agile",
            "scrum",
            "kanban",
            "jira",
            "confluence",
            "trello",
            "asana",
            "slack",
            "figma",
            "sketch",
            "photoshop",
            "illustrator",
            "indesign",
            "premiere",
            "after effects",
            "xd",
            "invision",
        ];

        // Common stopwords to ignore
        this.stopwords = new Set([
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "if",
            "because",
            "as",
            "what",
            "when",
            "where",
            "how",
            "why",
            "who",
            "which",
            "do",
            "does",
            "did",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "this",
            "that",
            "these",
            "those",
            "am",
            "in",
            "on",
            "at",
            "by",
            "for",
            "with",
            "about",
            "against",
            "between",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "to",
            "from",
            "up",
            "down",
            "of",
            "off",
            "over",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "all",
            "any",
            "both",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "s",
            "t",
            "can",
            "will",
            "just",
            "don",
            "should",
            "now",
            "tell",
            "me",
            "about",
            "describe",
            "explain",
            "give",
            "example",
        ]);
    }

    async extractTextFromFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onload = (event) => {
                const content = event.target.result;
                let text = "";

                if (file.type === "application/pdf") {
                    // PDF parsing would require pdf.js or similar library
                    // This is a simplified version that just extracts text from the PDF
                    // In a real implementation, you'd use a proper PDF parser
                    text = this._extractTextFromPDF(content);
                } else if (
                    file.type ===
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ) {
                    // DOCX parsing would require docx.js or similar library
                    // This is a simplified version
                    text = this._extractTextFromDOCX(content);
                } else if (file.type === "text/plain") {
                    text = content;
                } else {
                    reject(new Error("Unsupported file format"));
                }

                resolve(text);
            };

            reader.onerror = (error) => {
                reject(error);
            };

            if (file.type === "application/pdf") {
                reader.readAsArrayBuffer(file);
            } else {
                reader.readAsText(file);
            }
        });
    }

    _extractTextFromPDF(arrayBuffer) {
        // In a real implementation, you would use pdf.js here
        // This is a simplified version that just returns placeholder text
        console.warn(
            "PDF parsing requires pdf.js library in a real implementation"
        );
        return "Sample text extracted from PDF. Software Engineer with 5 years of experience in JavaScript and Python. Skills include React, Node.js, and AWS.";
    }

    _extractTextFromDOCX(arrayBuffer) {
        // In a real implementation, you would use docx.js here
        // This is a simplified version that just returns placeholder text
        console.warn(
            "DOCX parsing requires docx.js library in a real implementation"
        );
        return "Sample text extracted from DOCX. Data Scientist with expertise in machine learning and Python. Experience with TensorFlow and scikit-learn.";
    }

    extractRoleInfo(text) {
        const textLower = text.toLowerCase();
        const roleMatches = {};

        for (const [role, keywords] of Object.entries(this.roleKeywords)) {
            const matches = keywords.filter((keyword) =>
                textLower.includes(keyword.toLowerCase())
            ).length;

            if (matches > 0) {
                roleMatches[role] = matches;
            }
        }

        if (Object.keys(roleMatches).length > 0) {
            const bestRole = Object.entries(roleMatches).reduce((a, b) =>
                a[1] > b[1] ? a : b
            );
            return {
                role: bestRole[0],
                confidence: bestRole[1],
            };
        }

        return {
            role: "General",
            confidence: 0,
        };
    }

    extractSkills(text) {
        const textLower = text.toLowerCase();
        const foundSkills = [];

        // Find technical skills
        for (const skill of this.techSkills) {
            if (new RegExp(`\\b${skill}\\b`).test(textLower)) {
                foundSkills.push(skill);
            }
        }

        // Extract skills from skills section (simplified)
        const skillsSectionMatch = textLower.match(
            /skills[:\s]+(.*?)(?:\n\n|\Z)/s
        );
        if (skillsSectionMatch) {
            const skillsSection = skillsSectionMatch[1];

            // Extract bullet points or comma-separated items
            let skillItems = skillsSection
                .split(/[•\*\-]\s*/)
                .filter((item) => item.trim());
            if (skillItems.length <= 1) {
                // If no bullet points, try commas
                skillItems = skillsSection
                    .split(",")
                    .map((item) => item.trim());
            }

            for (const item of skillItems) {
                const cleanedItem = item.toLowerCase().trim();
                if (
                    cleanedItem &&
                    !foundSkills.includes(cleanedItem) &&
                    cleanedItem.length > 2 &&
                    !this.stopwords.has(cleanedItem)
                ) {
                    foundSkills.push(cleanedItem);
                }
            }
        }

        return foundSkills.slice(0, 10); // Return top 10 skills
    }

    async parseResume(file) {
        try {
            const text = await this.extractTextFromFile(file);
            const roleInfo = this.extractRoleInfo(text);
            const skills = this.extractSkills(text);

            return {
                text,
                roleInfo,
                skills,
            };
        } catch (error) {
            console.error("Error parsing resume:", error);
            return {
                text: "",
                roleInfo: { role: "General", confidence: 0 },
                skills: [],
            };
        }
    }
}

// Export for use in other files
if (typeof module !== "undefined" && module.exports) {
    module.exports = ResumeParser;
}
