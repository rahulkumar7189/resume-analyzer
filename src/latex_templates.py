"""
latex_templates.py
------------------
Three professional Jinja2 LaTeX resume templates.
- modern:  Sleek single-column with colored accent bar, Icons, and ruled sections
- classic: Traditional two-column, serif fonts, conservative layout
- tech:    Monospace-flavored dark-accent layout popular with SWE/ML candidates
"""
from jinja2 import Template

def _escape(text: str) -> str:
    """Escape LaTeX special characters in plain text."""
    if not isinstance(text, str):
        return ""
    replacements = [
        ('\\', r'\textbackslash{}'),
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\textasciitilde{}'),
        ('^', r'\^{}'),
        ('\u2019', "'"), ('\u2018', "'"),
        ('\u201C', "``"), ('\u201D', "''"),
        ('\u2013', '--'), ('\u2014', '---'),
        ('\u2011', '-'),
        ('\u00A0', ' '), ('\u202F', ' '), ('\u200B', ''),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


MODERN_TEMPLATE = r"""
\documentclass[10pt,a4paper]{article}
\usepackage{cmap}
\usepackage[margin=0.5in]{geometry}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{paracol}
\usepackage{tikz}
\usepackage[T1]{fontenc}
\usepackage{helvet}
\renewcommand{\familydefault}{\sfdefault}
\input{glyphtounicode}
\pdfgentounicode=1

% Premium Colors
\definecolor{primary}{HTML}{0F172A} % Slate 900
\definecolor{accent}{HTML}{0369A1}  % Sky 700
\definecolor{lightgray}{HTML}{F1F5F9} % Slate 100
\definecolor{textlight}{HTML}{475569} % Slate 600

\hypersetup{colorlinks=true, urlcolor=accent, linkcolor=accent}

% Section styling
\titleformat{\section}{\large\bfseries\color{primary}}{}{0em}{\MakeUppercase}[\vspace{-0.3\baselineskip}\color{accent}\titlerule\vspace{0.2\baselineskip}]
\titlespacing{\section}{0pt}{10pt}{4pt}

\setlist[itemize]{leftmargin=*,topsep=2pt,itemsep=3pt,parsep=0pt}
\pagestyle{empty}

% Skill pill tag
\newcommand{\skilltag}[1]{ %
  \tikz[baseline=(char.base)]\node[anchor=text,rectangle, fill=lightgray, rounded corners=2pt, inner sep=3pt] (char) {\small\textcolor{primary}{ #1}}; %
}

\begin{document}

% ── Header ──────────────────────────────────────────────────────────────
\begin{minipage}[t]{\textwidth}
  \begin{center}
    {\Huge\bfseries\color{primary} {{ name }} }\\[6pt]
    \normalsize\color{textlight}
    {% if email %}{{ email }}{% endif %}
    {% if phone %} $\cdot$ {{ phone }}{% endif %}
    {% if location %} $\cdot$ {{ location }}{% endif %}
    {% if linkedin %} $\cdot$ \href{ {{- linkedin -}} }{LinkedIn}{% endif %}
    {% if github %} $\cdot$ \href{ {{- github -}} }{GitHub}{% endif %}
  \end{center}
\end{minipage}
\vspace{12pt}

\columnratio{0.32}
\begin{paracol}{2}

% ── LEFT COLUMN ─────────────────────────────────────────────────────────
{% if skills %}
\section*{Skills}
{% for category, items in skills.items() %}
\textbf{\color{primary} {{- category -}} }\\[2pt]
{% for item in items %}
\skilltag{ {{- item | replace('\n', ' ') | replace('\r', '') -}} } 
{% endfor %}
\par\vspace{6pt}
{% endfor %}
{% endif %}

{% if education %}
\section*{Education}
{% for edu in education %}
\textbf{\color{primary} {{- edu.degree -}} }\\[2pt]
\textit{\color{textlight} {{- edu.institution -}} }\\[2pt]
{\small\color{textlight} {{- edu.dates -}} }
\vspace{6pt}
{% endfor %}
{% endif %}

{% if certifications %}
\section*{Certifications}
{% for cert in certifications %}
\textbf{\color{primary} {{- cert -}} }
\vspace{4pt}
{% endfor %}
{% endif %}

\switchcolumn

% ── RIGHT COLUMN ────────────────────────────────────────────────────────
{% if summary %}
\section*{Summary}
\color{primary}{{ summary }}
\vspace{6pt}
{% endif %}

{% if experience %}
\section*{Experience}
{% for job in experience %}
\noindent\textbf{\large\color{primary} {{- job.title -}} } \hfill {\small\color{accent} {{- job.dates -}} }\\[2pt]
\textit{\color{textlight} {{- job.company -}} }
\vspace{2pt}
\begin{itemize}
{% for bullet in job.bullets %}  \item \color{primary}{{ bullet }}
{% endfor %}\end{itemize}
\vspace{6pt}
{% endfor %}
{% endif %}

{% if projects %}
\section*{Projects}
{% for proj in projects %}
\noindent\textbf{\large\color{primary} {{- proj.title -}} }
\vspace{2pt}
\begin{itemize}
{% for bullet in proj.bullets %}  \item \color{primary}{{ bullet }}
{% endfor %}\end{itemize}
\vspace{6pt}
{% endfor %}
{% endif %}

\end{paracol}
\end{document}
"""

CLASSIC_TEMPLATE = r"""
\documentclass[11pt,a4paper]{article}
\usepackage{cmap}
\usepackage[margin=0.75in]{geometry}
\usepackage{times}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage[T1]{fontenc}
\input{glyphtounicode}
\pdfgentounicode=1
\hypersetup{colorlinks=false}
\titleformat{\section}{\normalsize\bfseries\uppercase}{}{0em}{}[\hrule]
\titlespacing{\section}{0pt}{8pt}{4pt}
\setlist[itemize]{leftmargin=*,topsep=2pt,itemsep=0pt,parsep=0pt}
\pagestyle{empty}
\begin{document}

% ── Header ──────────────────────────────────────────────────────────────
{\centering
  {\Large\textbf{ {{ name }} }}\\[3pt]
  \small
  {% if email %}{{ email }}{% endif %}
  {% if phone %} | {{ phone }}{% endif %}
  {% if location %} | {{ location }}{% endif %}
  {% if linkedin %} | \href{ {{- linkedin -}} }{LinkedIn}{% endif %}
  {% if github %} | \href{ {{- github -}} }{GitHub}{% endif %}
  \par
}
\vspace{4pt}

{% if summary %}
\section{Objective}
{{ summary }}
{% endif %}

{% if experience %}
\section{Professional Experience}
{% for job in experience %}
\textbf{ {{- job.title -}} }, \textit{ {{- job.company -}} } \hfill {{ job.dates }}
\begin{itemize}
{% for bullet in job.bullets %}  \item {{ bullet }}
{% endfor %}\end{itemize}
{% endfor %}
{% endif %}

{% if projects %}
\section{Projects}
{% for proj in projects %}
\textbf{ {{- proj.title -}} }
\begin{itemize}
{% for bullet in proj.bullets %}  \item {{ bullet }}
{% endfor %}\end{itemize}
{% endfor %}
{% endif %}

{% if education %}
\section{Education}
{% for edu in education %}
\textbf{ {{- edu.degree -}} }, \textit{ {{- edu.institution -}} } \hfill {{ edu.dates }}
{% if edu.details %}\begin{itemize}
{% for d in edu.details %}  \item {{ d }}
{% endfor %}\end{itemize}{% endif %}
{% endfor %}
{% endif %}

{% if skills %}
\section{Technical Skills}
{% for category, items in skills.items() %}
\textbf{ {{- category -}} :} {{ items | join(', ') }}\\
{% endfor %}
{% endif %}

{% if certifications %}
\section{Certifications \& Awards}
\begin{itemize}
{% for cert in certifications %}  \item {{ cert }}
{% endfor %}\end{itemize}
{% endif %}

\end{document}
"""

TECH_TEMPLATE = r"""
\documentclass[10pt,a4paper]{article}
\usepackage{cmap}
\usepackage[margin=0.6in]{geometry}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage[T1]{fontenc}
\input{glyphtounicode}
\pdfgentounicode=1
\usepackage{lmodern}
\usepackage{mdframed}
\definecolor{techblue}{RGB}{30, 100, 200}
\definecolor{techgray}{RGB}{50, 50, 50}
\definecolor{codetag}{RGB}{0, 120, 180}
\hypersetup{colorlinks=true, urlcolor=techblue}
\titleformat{\section}{\bfseries\color{techblue}\normalsize}{}{0em}{$\triangleright$~}[\color{techblue}\titlerule]
\titlespacing{\section}{0pt}{8pt}{4pt}
\setlist[itemize]{leftmargin=*,topsep=2pt,itemsep=1pt,parsep=0pt,label=\textcolor{techblue}{--}}
\pagestyle{empty}
\begin{document}

% ── Header ──────────────────────────────────────────────────────────────
\begin{center}
  {\huge\bfseries\color{techgray} {{ name }} }\\[4pt]
  \small\ttfamily
  {% if email %}{\color{techblue} {{- email -}} }{% endif %}
  {% if phone %} $|$ {{ phone }}{% endif %}
  {% if location %} $|$ {{ location }}{% endif %}
  {% if github %} $|$ \href{ {{- github -}} }{github}{% endif %}
  {% if linkedin %} $|$ \href{ {{- linkedin -}} }{linkedin}{% endif %}
\end{center}
\normalfont

{% if summary %}
\section{Profile}
{{ summary }}
{% endif %}

{% if experience %}
\section{Experience}
{% for job in experience %}
\textbf{\color{techgray} {{- job.title -}} } \textcolor{techblue}{@} \textit{ {{- job.company -}} } \hfill \texttt{ {{- job.dates -}} }
\begin{itemize}
{% for bullet in job.bullets %}  \item {{ bullet }}
{% endfor %}\end{itemize}
{% endfor %}
{% endif %}

{% if projects %}
\section{Projects}
{% for proj in projects %}
\textbf{\color{techgray} {{- proj.title -}} }
\begin{itemize}
{% for bullet in proj.bullets %}  \item {{ bullet }}
{% endfor %}\end{itemize}
{% endfor %}
{% endif %}

{% if skills %}
\section{Skills \& Technologies}
{% for category, items in skills.items() %}
\textbf{\color{techgray} {{- category -}} :} \textcolor{codetag}{ {{- items | join(' / ') -}} }\\
{% endfor %}
{% endif %}

{% if education %}
\section{Education}
{% for edu in education %}
\textbf{ {{- edu.degree -}} } --- \textit{ {{- edu.institution -}} } \hfill \texttt{ {{- edu.dates -}} }
{% if edu.details %}\begin{itemize}
{% for d in edu.details %}  \item {{ d }}
{% endfor %}\end{itemize}{% endif %}
{% endfor %}
{% endif %}

{% if certifications %}
\section{Certifications}
\begin{itemize}
{% for cert in certifications %}  \item {{ cert }}
{% endfor %}\end{itemize}
{% endif %}

\end{document}
"""

PREMIUM_TEMPLATE = r"""
\documentclass[10pt,a4paper]{article}
\usepackage{cmap}
\usepackage[margin=0.5in]{geometry}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage[T1]{fontenc}
\input{glyphtounicode}
\pdfgentounicode=1
\usepackage{lmodern}
\usepackage{tikz}
\usepackage{parskip}
\usepackage{paracol}

\definecolor{headerbg}{RGB}{43, 45, 66}
\definecolor{headertext}{RGB}{237, 242, 244}
\definecolor{accent}{RGB}{239, 35, 60}
\definecolor{textmain}{RGB}{43, 45, 66}
\definecolor{textlight}{RGB}{141, 153, 174}

\renewcommand{\familydefault}{\sfdefault}
\pagestyle{empty}

\titleformat{\section}{\Large\bfseries\color{accent}}{}{0em}{}[\vspace{-0.5em}\rule{\linewidth}{1.5pt}]
\titlespacing{\section}{0pt}{12pt}{6pt}
\setlist[itemize]{leftmargin=*,topsep=2pt,itemsep=2pt,parsep=0pt}

\begin{document}

% ── HEADER ──────────────────────────────────────────────────────────────
\begin{tikzpicture}[remember picture,overlay]
    \fill[headerbg] (current page.north west) rectangle ([yshift=-1.75in]current page.north east);
\end{tikzpicture}

\vspace*{-0.3in}
\begin{center}
    {\Huge \color{headertext}\textbf{ {{ name }} }}\\[0.15in]
    {\footnotesize \color{headertext} {% if location %}{{ location }}{% endif %} {% if phone %}$\cdot$ {{ phone }}{% endif %} {% if email %}$\cdot$ {{ email }}{% endif %} {% if linkedin %}$\cdot$ \href{ {{ linkedin }} }{LinkedIn}{% endif %} {% if github %}$\cdot$ \href{ {{ github }} }{GitHub}{% endif %} }\\[0.15in]
    {% if summary %}{\small \color{textlight} {{ summary | truncate(150) }} }{% endif %}
\end{center}

\vspace{0.7in}

% ── TWO COLUMN LAYOUT ───────────────────────────────────────────────────
\columnratio{0.31}
\setlength{\columnsep}{0.04\textwidth}
\begin{paracol}{2}
    {% if skills %}
    \section*{Skills}
    {% for category, items in skills.items() %}
    \textbf{\color{textmain} {{ category }} }\\
    {\color{textlight} \small {{ items | join(', ') }} }\\[8pt]
    {% endfor %}
    {% endif %}
    
    {% if education %}
    \section*{Education}
    {% for edu in education %}
    \textbf{\color{textmain} {{ edu.degree }} }\\
    {\color{textlight} \small {{ edu.institution }} }\\
    {\color{accent} \footnotesize {{ edu.dates }} }\\[8pt]
    {% endfor %}
    {% endif %}
    
    {% if certifications %}
    \section*{Certifications}
    \begin{itemize}[leftmargin=*, label=\textcolor{accent}{$\bullet$}]
    {% for cert in certifications %}  \item {\small \color{textmain} {{ cert }} }
    {% endfor %}\end{itemize}
    {% endif %}

\switchcolumn
    {% if summary %}
    \section*{Profile}
    \small \color{textmain} {{ summary }} 
    \vspace{0.15in}
    {% endif %}

    {% if experience %}
    \section*{Experience}
    {% for job in experience %}
    \textbf{\large\color{textmain} {{ job.title }} } \hfill {\color{accent} \small\textbf{ {{ job.dates }} }}\\
    \textit{\color{textlight} {{ job.company }} }\\[4pt]
    \small \color{textmain}
    \begin{itemize}[leftmargin=*, label=\textcolor{textlight}{-}]
    {% for bullet in job.bullets %}  \item {{ bullet }}
    {% endfor %}\end{itemize}
    \vspace{0.15in}
    {% endfor %}
    {% endif %}
    
    {% if projects %}
    \section*{Projects}
    {% for proj in projects %}
    \textbf{\large\color{textmain} {{ proj.title }} }\\[4pt]
    \small \color{textmain}
    \begin{itemize}[leftmargin=*, label=\textcolor{textlight}{-}]
    {% for bullet in proj.bullets %}  \item {{ bullet }}
    {% endfor %}\end{itemize}
    \vspace{0.15in}
    {% endfor %}
    {% endif %}
\end{paracol}

\end{document}
"""

TEMPLATES = {
    "modern": MODERN_TEMPLATE,
    "classic": CLASSIC_TEMPLATE,
    "tech": TECH_TEMPLATE,
    "premium": PREMIUM_TEMPLATE,
}

def render_template(template_name: str, resume_data: dict) -> str:
    """
    Renders a LaTeX resume template using Jinja2.
    resume_data keys: name, email, phone, location, linkedin, github,
                      summary, experience (list), education (list),
                      skills (dict), certifications (list)
    """
    raw = TEMPLATES.get(template_name, MODERN_TEMPLATE)
    tpl = Template(raw)
    return tpl.render(**resume_data)
