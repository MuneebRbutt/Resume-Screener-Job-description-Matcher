import re

# Regex patterns to detect section headers
SECTION_PATTERNS = {
    'skills': [
        r'\b(technical\s+)?skills?\b',
        r'\bcore\s+competenc(y|ies)\b',
        r'\btechnologies\b',
        r'\bproficienc(y|ies)\b',
        r'\bexpertise\b',
    ],
    'experience': [
        r'\b(work\s+|professional\s+|relevant\s+)?experience\b',
        r'\bemployment(\s+history)?\b',
        r'\bwork\s+history\b',
        r'\bcareer\b',
    ],
    'education': [
        r'\beducation(\s+background)?\b',
        r'\bacademic(\s+background)?\b',
        r'\bqualifications?\b',
    ],
    'projects': [
        r'\bprojects?\b',
        r'\bportfolio\b',
    ],
    'certifications': [
        r'\bcertifications?\b',
        r'\bcourses?\b',
        r'\btraining\b',
        r'\bachievements?\b',
    ],
    'summary': [
        r'\b(professional\s+)?summary\b',
        r'\bobjective\b',
        r'\bprofile\b',
        r'\babout\s+me\b',
    ],
}

# How much each section contributes to the final score
# Skills + Experience = 80% of the score, just like real ATS
SECTION_WEIGHTS = {
    'skills':           0.45,
    'experience':       0.35,
    'projects':         0.10,
    'education':        0.08,
    'certifications':   0.02,
    'summary':          0.00,  # Objective statements are noise — ignore
    'unknown':          0.00,
}


def detect_section_header(line):
    """
    Returns section name if the line looks like a header, else None.
    Headers are short lines (≤6 words) that match known patterns.
    """
    words = line.split()
    if len(words) > 6:
        return None

    line_lower = line.lower().strip(':').strip('-').strip()

    for section, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, line_lower):
                return section

    return None


def parse_sections(text):
    """
    Splits resume text into labelled sections.
    Returns dict: { section_name: text_content }

    Example output:
    {
        'skills':     'Python, TensorFlow, PyTorch ...',
        'experience': 'ML Engineer at TechCorp ...',
        'education':  'BS Computer Science ...',
    }
    """
    lines = text.split('\n')
    sections = {}
    current_section = 'unknown'
    current_lines = []

    for line in lines:
        stripped = line.strip()
        detected = detect_section_header(stripped) if stripped else None

        if detected:
            # Save whatever we collected for the previous section
            content = '\n'.join(current_lines).strip()
            if content:
                sections[current_section] = sections.get(current_section, '') + '\n' + content

            # Start fresh for new section
            current_section = detected
            current_lines = []
        else:
            current_lines.append(line)

    # Save the final section
    content = '\n'.join(current_lines).strip()
    if content:
        sections[current_section] = sections.get(current_section, '') + '\n' + content

    return sections