# Pipeline de requête

import os
import re
import unicodedata
import ollama
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MAX_CONTEXT_DOCS = 3
MAX_DOC_CHARS = 800
MAX_TOTAL_CONTEXT_CHARS = 2400
HINT_KEYWORDS = {
    "rgpd": ["rgpd", "règlement", "reglement", "article", "chapitre"],
    "recrut": ["recrut", "cv", "candidat", "embauche"],
    "video": ["vidéo", "video", "caméra", "camera", "surveillance", "cse", "comité"],
    "securite": ["sécurité", "securite", "violation", "mesure technique"],
    "conservation": ["conservation", "durée", "duree", "archivage"],
    "sante": ["santé", "sante", "médical", "medical"],
}
SOURCE_TYPE_BY_HINT = {
    "rgpd": {"reglement_officiel", "cnil_general"},
    "recrut": {"recrutement", "reglement_officiel", "cnil_general"},
    "video": {"videosurveillance", "reglement_officiel", "cnil_general"},
    "securite": {"securite", "owasp", "reglement_officiel", "cnil_general"},
    "conservation": {"conservation", "reglement_officiel", "cnil_general"},
    "sante": {"sante", "reglement_officiel", "cnil_general"},
}

def classify_source(source_name: str) -> str:
    normalized = source_name.lower()
    if "reglement" in normalized or "rgpd" in normalized:
        return "reglement_officiel"
    if "recrut" in normalized or "cv" in normalized:
        return "recrutement"
    if "video" in normalized or "cam" in normalized or "surveillance" in normalized:
        return "videosurveillance"
    if "conservation" in normalized or "durée" in normalized or "duree" in normalized:
        return "conservation"
    if "sante" in normalized or "medical" in normalized or "médical" in normalized:
        return "sante"
    if "securite" in normalized or "sécurité" in normalized or "violation" in normalized:
        return "securite"
    if "owasp" in normalized:
        return "owasp"
    if "cnil" in normalized:
        return "cnil_general"
    return "autre"

def extract_document_hints(question: str) -> list[str]:
    normalized = normalize_text(question)
    hints = []
    for hint, keywords in HINT_KEYWORDS.items():
        if any(normalize_text(keyword) in normalized for keyword in keywords):
            hints.append(hint)
    return hints

def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))

def document_matches_hints(doc, hints: list[str]) -> bool:
    if not hints:
        return True

    source_name = doc.metadata.get("source_name") or os.path.basename(
        doc.metadata.get("source", "Document inconnu")
    )
    source_type = classify_source(source_name)
    haystack = normalize_text(f"{source_name}\n{doc.page_content}")

    for hint in hints:
        allowed_source_types = SOURCE_TYPE_BY_HINT.get(hint, set())
        keywords = HINT_KEYWORDS.get(hint, [])
        if source_type in allowed_source_types and any(normalize_text(keyword) in haystack for keyword in keywords):
            return True

    return False

def filter_ranked_documents(question: str, ranked: list[tuple]) -> list[tuple]:
    hints = extract_document_hints(question)
    if not ranked:
        return []

    best_score = ranked[0][1]
    filtered = []

    for doc, score in ranked:
        thematic_match = document_matches_hints(doc, hints)
        within_relative_threshold = score <= best_score + 0.12

        if hints:
            if thematic_match and within_relative_threshold:
                filtered.append((doc, score))
            elif thematic_match and len(filtered) < 2:
                filtered.append((doc, score))
        elif within_relative_threshold:
            filtered.append((doc, score))

    if filtered:
        return filtered[:4]

    return ranked[:2]

def get_source_bonus(source_type: str, hints: list[str]) -> float:
    bonus = 0.0

    if "rgpd" in hints:
        if source_type == "reglement_officiel":
            bonus -= 0.22
        elif source_type == "cnil_general":
            bonus -= 0.06
        elif source_type == "owasp":
            bonus += 0.22

    if "video" in hints:
        if source_type == "videosurveillance":
            bonus -= 0.20
        elif source_type == "owasp":
            bonus += 0.18

    if "recrut" in hints:
        if source_type == "recrutement":
            bonus -= 0.20
        elif source_type == "owasp":
            bonus += 0.18

    if "conservation" in hints:
        if source_type == "conservation":
            bonus -= 0.18
        elif source_type == "owasp":
            bonus += 0.15

    if "sante" in hints:
        if source_type == "sante":
            bonus -= 0.18
        elif source_type == "owasp":
            bonus += 0.15

    if "securite" in hints:
        if source_type in {"securite", "owasp"}:
            bonus -= 0.12

    return bonus

def rank_documents(question: str, vectorstore):
    docs_with_scores = vectorstore.similarity_search_with_score(question, k=10)
    hints = extract_document_hints(question)
    ranked = []

    for doc, score in docs_with_scores:
        source_name = doc.metadata.get("source_name") or os.path.basename(
            doc.metadata.get("source", "Document inconnu")
        )
        source_name_lower = source_name.lower()
        source_type = classify_source(source_name)
        bonus = get_source_bonus(source_type, hints)

        if hints and any(hint in source_name_lower for hint in hints):
            bonus -= 0.08

        if "source:" in doc.page_content.lower():
            bonus -= 0.02

        if source_type == "reglement_officiel":
            bonus -= 0.05
        elif source_type == "cnil_general" and hints and not {"rgpd", "securite"}.intersection(hints):
            bonus += 0.06
        elif source_type == "autre":
            bonus += 0.05

        ranked.append((doc, score + bonus))

    ranked.sort(key=lambda item: item[1])
    ranked = filter_ranked_documents(question, ranked)

    selected = []
    seen_sources = set()

    for doc, score in ranked:
        source_name = doc.metadata.get("source_name") or os.path.basename(
            doc.metadata.get("source", "Document inconnu")
        )
        if source_name not in seen_sources or len(selected) < 3:
            selected.append((doc, score))
            seen_sources.add(source_name)
        if len(selected) >= 5:
            break

    if len(selected) < 5:
        for doc, score in ranked:
            if (doc, score) not in selected:
                selected.append((doc, score))
            if len(selected) >= 5:
                break

    return selected

def format_source_label(doc) -> str:
    source_name = doc.metadata.get("source_name") or os.path.basename(
        doc.metadata.get("source", "Document inconnu")
    )
    page_number = doc.metadata.get("page_number")
    if page_number is not None:
        return f"{source_name} (p. {page_number})"
    return source_name

def extract_key_terms(question: str) -> list[str]:
    """Extrait les acronymes et termes-clés de la question pour ancrage forcé."""
    terms = []
    # Acronymes en majuscules (CSE, CNIL, DPO, etc.)
    acronyms = re.findall(r'\b[A-ZÀ-Ü]{2,}\b', question)
    terms.extend(acronyms)
    # Termes importants entre guillemets
    quoted = re.findall(r'[«"](.*?)[»"]', question)
    terms.extend(quoted)
    return list(set(terms))

def extract_article_references(question: str) -> list[str]:
    """Extrait les références d'articles mentionnées dans la question."""
    patterns = [
        r"article\s+(\d+(?:\s*(?:bis|ter|quater|quinquies))?)",
        r"art\.?\s*(\d+(?:\s*(?:bis|ter|quater|quinquies))?)",
        r"paragraphe\s+(\d+)",
        r"chapitre\s+([IVXLCDM]+|\d+)",
    ]
    refs = []
    q_lower = question.lower()
    for pattern in patterns:
        matches = re.findall(pattern, q_lower)
        for m in matches:
            refs.append(m.strip())
    return refs

def is_verification_question(question: str) -> bool:
    """Détecte si la question demande de confirmer/infirmer une affirmation."""
    q_lower = question.lower()
    verification_patterns = [
        r"interdit-(?:il|elle)",
        r"autorise-t-(?:il|elle)",
        r"remplace-t-(?:il|elle)",
        r"est-(?:il|elle)\s+(?:vrai|exact|correct|obligatoire|possible|valable|valide|applicable|suffisant|n[eé]cessaire|l[eé]gal|conforme|autoris[eé]|interdit|permis)",
        r"est-ce\s+(?:que|vrai)",
        r"peut-on",
        r"doit-on",
        r"faut-il",
        r"a-t-(?:il|elle|on)",
        r"(?:le|la|les|un|une)\s+\w+\s+(?:est-il|est-elle)\s+",
        r"l'article\s+\d+.*(?:interdit|autorise|impose|pr[eé]voit|stipule)",
    ]
    return any(re.search(p, q_lower) for p in verification_patterns)

def neutralize_question(question: str) -> str:
    """Réécrit les questions de vérification en forme neutre pour éviter le biais de confirmation."""
    refs = extract_article_references(question)
    if not refs or not is_verification_question(question):
        return question

    # Extraire le sujet de la question (après le verbe de vérification)
    q_lower = question.lower()
    # Patterns courants : "L'article X interdit-il Y ?" -> "Que disent les documents sur Y ?"
    subject_patterns = [
        r"l'article\s+\d+[^?]*(?:interdit|autorise|impose|prévoit|stipule)[^?]*?(?:le|la|les|l'|du|de|des|un|une)\s+(.+?)\s*\?",
        r"(?:interdit|autorise|impose)-(?:t-)?(?:il|elle)[^?]*?(?:le|la|les|l'|du|de|des|un|une)\s+(.+?)\s*\?",
    ]
    subject = None
    for pattern in subject_patterns:
        match = re.search(pattern, q_lower)
        if match:
            subject = match.group(1).strip()
            break

    if subject:
        refs_str = ", ".join(f"article {r}" for r in refs)
        return f"Que disent les documents sur {subject} ? Le {refs_str} du RGPD en parle-t-il ?"

    return question

def validate_answer(question: str, answer: str, context: str) -> str:
    """Post-validation : détecte les hallucinations sur les questions de vérification
    et les références à des articles inexistants dans le contexte."""
    refs = extract_article_references(question)
    is_verif = is_verification_question(question)

    # FILTRE 1 : articles référencés dans la question mais ABSENTS du contexte
    if refs:
        context_lower = context.lower()
        missing_refs = []
        for ref in refs:
            ref_patterns = [f"article {ref}", f"art. {ref}", f"art {ref}"]
            if not any(p in context_lower for p in ref_patterns):
                missing_refs.append(ref)

        if missing_refs:
            refs_str = ", ".join(f"article {r}" for r in missing_refs)
            return (
                f"[!] **Reference introuvable** : le {refs_str} mentionne dans votre question "
                f"n'apparait pas dans les documents de la base documentaire.\n\n"
                f"Le modele ne peut pas repondre sur un article qui n'est pas present "
                f"dans les sources indexees. Il est possible que cet article n'existe pas "
                f"ou qu'il ne soit pas couvert par la base documentaire actuelle.\n\n"
                f"-> Conseil : verifiez que cet article existe dans le RGPD, ou reformulez "
                f"votre question sans reference a un article precis."
            )

    # FILTRE 2 : references juridiques inventees dans la REPONSE
    answer_fabricated = _detect_fabricated_references(answer, context)
    if answer_fabricated:
        return answer_fabricated

    # FILTRE 2b : ancrage sujet - termes-cles de la question absents du contexte
    grounding_block = _check_subject_grounding(question, answer, context)
    if grounding_block:
        return grounding_block

    # FILTRE 3 : questions de verification (oui/non)
    if not is_verif:
        return answer

    answer_lower = answer.lower().strip()
    affirmative_start = any(
        answer_lower.startswith(prefix)
        for prefix in ["oui", "en effet", "effectivement", "c'est exact", "absolument",
                       "1. oui", "1. r\u00e9sum\u00e9", "r\u00e9sum\u00e9 de la r\u00e9ponse : oui"]
    )
    # Aussi détecter "Résumé : Oui" ou "1. Résumé de la réponse : Oui"
    if not affirmative_start and "oui" in answer_lower[:80]:
        affirmative_start = True

    if not affirmative_start:
        # Réponse non affirmative -> ajouter un simple disclaimer
        disclaimer = (
            "\n\n---\n\u26a0\ufe0f *Avertissement : cette réponse est générée par un modèle local "
            "qui peut se tromper. Vérifiez dans le texte officiel du RGPD.*"
        )
        return answer + disclaimer

    # Réponse affirmative à une question de vérification -> BLOQUER
    if refs:
        refs_str = ", ".join(f"article {r}" for r in refs)
        return (
            f"\u26a0\ufe0f **Vérification non fiable** : le modèle local a tendance à confirmer "
            f"les affirmations contenues dans les questions sans vérifier leur exactitude.\n\n"
            f"**Ce que disent réellement les documents récupérés :**\n\n"
            f"{_extract_relevant_passages(context, refs)}\n\n"
            f"-> Conseil : reformulez en question ouverte, ex: 'Que dit le {refs_str} du RGPD ?'"
        )
    else:
        # Pas d'article spécifique mais question de vérification + "Oui"
        return (
            f"\u26a0\ufe0f **Vérification non fiable** : le modèle local a tendance à confirmer "
            f"les affirmations contenues dans les questions sans vérifier leur exactitude.\n\n"
            f"La réponse générée commençait par 'Oui' mais cette confirmation n'est pas garantie "
            f"par les documents de la base.\n\n"
            f"**Extraits des documents récupérés :**\n\n"
            f"{_extract_context_summary(context)}\n\n"
            f"-> Conseil : reformulez en question ouverte pour obtenir une réponse factuelle, "
            f"ex: 'Quelles sont les conditions de transfert de données hors UE ?'"
        )

def _check_subject_grounding(question: str, answer: str, context: str) -> str | None:
    """Verifie que les sujets specifiques de la question sont presents dans le contexte.
    Si des termes-cles importants (pays, ages, concepts specifiques) sont absents
    du contexte mais que le modele repond quand meme, bloque la reponse."""
    q_lower = question.lower()
    context_lower = context.lower()
    answer_lower = answer.lower()

    # Ne pas bloquer si le modele dit deja "non trouve"
    if "information non trouv" in answer_lower or "non trouvee dans les sources" in answer_lower:
        return None

    missing_subjects = []

    # 1. Noms de pays specifiques (hors France/UE qui sont generiques)
    country_patterns = [
        ("portugal", "portugal"), ("espagne", "espagne"), ("allemagne", "allemagne"),
        ("italie", "italie"), ("belgique", "belgique"), ("luxembourg", "luxembourg"),
        ("pays-bas", "pays-bas"), ("suisse", "suisse"), ("royaume-uni", "royaume-uni"),
        ("etats-unis", "etats-unis|usa|\\bus\\b"), ("chine", "chine"),
        ("japon", "japon"), ("canada", "canada"), ("bresil", "bresil|br[eé]sil"),
        ("inde", "\\binde\\b"), ("russie", "russie"), ("irlande", "irlande"),
    ]
    for country_name, pattern in country_patterns:
        if re.search(pattern, q_lower):
            if country_name not in context_lower:
                missing_subjects.append(country_name)

    # 2. Ages specifiques (mineur de X ans)
    age_match = re.search(r"(\d+)\s*ans", q_lower)
    if age_match:
        age = age_match.group(1)
        if age not in context_lower:
            missing_subjects.append(f"{age} ans")

    # 3. Mot "mineur" si la question en parle
    if "mineur" in q_lower and "mineur" not in context_lower:
        missing_subjects.append("mineur")

    if not missing_subjects:
        return None

    # Au moins 2 termes manquants, ou 1 terme pays manquant -> bloquer
    has_country_missing = any(s in [c[0] for c in country_patterns] for s in missing_subjects)
    if len(missing_subjects) >= 2 or has_country_missing:
        terms_str = ", ".join(missing_subjects)
        return (
            f"[!] **Information non verifiable** : les termes ({terms_str}) "
            f"mentionnes dans votre question n'apparaissent pas dans les documents "
            f"de la base documentaire.\n\n"
            f"Le modele ne dispose pas d'informations specifiques sur ce sujet "
            f"et risque d'inventer une reponse.\n\n"
            f"-> Conseil : la base documentaire couvre principalement le RGPD "
            f"et les guides CNIL pour la France. Pour des questions specifiques "
            f"a un pays, consultez l'autorite de protection des donnees de ce pays."
        )

    return None


def _detect_fabricated_references(answer: str, context: str) -> str | None:
    """Detecte les references juridiques dans la reponse qui n'existent pas dans le contexte.
    Retourne un message de remplacement si des references inventees sont trouvees, sinon None."""
    answer_lower = answer.lower()
    context_lower = context.lower()

    # Patterns pour detecter des references juridiques dans la reponse
    legal_ref_patterns = [
        # "loi n° 67/2001", "loi n° 58/2019", "loi n 78-17"
        r"loi\s+n[°o]?\s*(\d[\d\-/]+\d)",
        # "reglement n° 67/2001", "reglement portugais n° ..."
        r"r[eè]glement[^.]{0,30}n[°o]?\s*(\d[\d\-/]+\d)",
        # "directive 95/46", "directive eprivacy"
        r"directive\s+(\d+/\d+(?:/\w+)?)",
        # "decret n° 2018-687"
        r"d[eé]cret\s+n[°o]?\s*(\d[\d\-/]+\d)",
        # "article 8-a", "article 78 bis" (references composees inhabituelles)
        r"article\s+(\d+\s*-\s*[a-z])",
    ]

    fabricated_refs = []
    for pattern in legal_ref_patterns:
        matches = re.findall(pattern, answer_lower)
        for match in matches:
            # Verifier si cette reference existe dans le contexte
            if match not in context_lower:
                fabricated_refs.append(match)

    if fabricated_refs:
        refs_list = ", ".join(fabricated_refs[:3])
        return (
            f"[!] **Reponse bloquee** : le modele a cite des references juridiques "
            f"({refs_list}) qui n'apparaissent pas dans les documents de la base.\n\n"
            f"Ces references sont probablement inventees par le modele. "
            f"Le modele local a tendance a fabriquer des numeros de loi, de decret "
            f"ou d'article pour paraitre plus credible.\n\n"
            f"-> Conseil : ne vous fiez pas a ces references. Reformulez votre question "
            f"de maniere plus generale ou consultez directement le texte officiel du RGPD."
        )

    # Sous-articles enumeres dans la reponse (ex: "6.1 a", "6.1.b", "article 6, 1, f")
    sub_article_patterns = [
        r"article\s+\d+[\.\,]?\s*\d*\s*[,\.]?\s*([a-f])\s*\)",
        r"(\d+\.\d+)\s+([a-f])\)",
        r"(\d+\.\d+)\s*\(?([a-f])\)?",
    ]
    answer_subrefs = set()
    for pattern in sub_article_patterns:
        matches = re.findall(pattern, answer_lower)
        for match in matches:
            if isinstance(match, tuple):
                subref = " ".join(match).strip()
            else:
                subref = match.strip()
            answer_subrefs.add(subref)

    if len(answer_subrefs) >= 3:
        missing_subrefs = []
        for subref in answer_subrefs:
            parts = subref.split()
            found = False
            for part in parts:
                if len(part) == 1 and part.isalpha():
                    search_patterns = [
                        f"{part})",
                        f"{part} )",
                    ]
                    if any(sp in context_lower for sp in search_patterns):
                        found = True
                        break
            if not found:
                if subref not in context_lower:
                    missing_subrefs.append(subref)

        if len(missing_subrefs) > len(answer_subrefs) // 2:
            return (
                f"[!] **Reponse potentiellement inexacte** : le modele a enumere "
                f"{len(answer_subrefs)} sous-articles mais la majorite "
                f"n'apparaissent pas dans les documents recuperes.\n\n"
                f"Le modele a probablement complete la liste a partir de ses "
                f"connaissances generales, qui peuvent etre incorrectes ou incompletes.\n\n"
                f"-> Conseil : consultez directement le texte officiel du RGPD pour "
                f"obtenir la liste exacte et complete des conditions."
            )

    return None


def _extract_relevant_passages(context: str, refs: list[str]) -> str:
    """Extrait les passages du contexte qui mentionnent les articles référencés."""
    lines = context.split("\n")
    relevant = []
    for line in lines:
        line_lower = line.lower()
        for ref in refs:
            if f"article {ref}" in line_lower or f"art. {ref}" in line_lower:
                cleaned = line.strip()
                if cleaned and len(cleaned) > 20:
                    relevant.append(f"- {cleaned[:300]}")
                    break

    if relevant:
        return "\n".join(relevant[:4])
    return "Aucun passage mentionnant explicitement cet article n'a été trouvé dans les extraits récupérés."

def _check_source_relevance(question: str, docs: list) -> list:
    """Verifie si les documents recuperes contiennent les concepts cles de la question.
    Retourne la liste des docs avec un flag de pertinence."""
    q_lower = question.lower()
    # Extraire les concepts specifiques (noms propres, termes techniques)
    concept_patterns = [
        r'\b(eprivacy|e-privacy)\b',
        r'\b(bcr|binding corporate rules)\b',
        r'\b(privacy shield)\b',
        r'\b(safe harbor)\b',
        r'\b(bouclier de confidentialit[eé])\b',
        r'\b(clause[s]? contractuelle[s]? type[s]?)\b',
        r'\b(analyse d\'impact|aipd|pia)\b',
        r'\b(d[eé]l[eé]gu[eé] [aà] la protection)\b',
    ]
    key_concepts = []
    for pattern in concept_patterns:
        if re.search(pattern, q_lower):
            match = re.search(pattern, q_lower)
            key_concepts.append(match.group(1))

    # Aussi extraire les noms/termes entre guillemets ou en majuscules specifiques
    quoted = re.findall(r'[«"](.*?)[»"]', question)
    key_concepts.extend([q.lower() for q in quoted])

    if not key_concepts:
        return docs  # Pas de concept specifique -> on ne filtre pas

    relevant_docs = []
    for doc in docs:
        content_lower = doc.page_content.lower()
        source_lower = (doc.metadata.get("source_name", "") or
                       os.path.basename(doc.metadata.get("source", ""))).lower()
        combined = content_lower + " " + source_lower
        if any(concept in combined for concept in key_concepts):
            relevant_docs.append(doc)

    return relevant_docs


def _extract_context_summary(context: str) -> str:
    """Extrait un résumé des passages clés du contexte récupéré."""
    lines = [l.strip() for l in context.split("\n") if l.strip() and len(l.strip()) > 30]
    if not lines:
        return "Aucun extrait pertinent trouvé dans les documents récupérés."
    selected = lines[:5]
    return "\n".join(f"- {line[:250]}" for line in selected)

def build_llm_context(docs: list) -> str:
    context_parts = []
    total_chars = 0

    for doc in docs[:MAX_CONTEXT_DOCS]:
        content = doc.page_content.strip()
        if len(content) > MAX_DOC_CHARS:
            content = f"{content[:MAX_DOC_CHARS].rstrip()} [...]"

        part = f"[Source: {format_source_label(doc)}]\n{content}"
        if total_chars + len(part) > MAX_TOTAL_CONTEXT_CHARS:
            remaining = MAX_TOTAL_CONTEXT_CHARS - total_chars
            if remaining <= 0:
                break
            part = part[:remaining].rstrip()
            context_parts.append(part)
            break

        context_parts.append(part)
        total_chars += len(part)

    return "\n\n".join(context_parts)

def build_prompt(question: str, domaine_context: str, contexte: str, historique_formate: str) -> tuple[str, str]:
    """Retourne (system_message, user_message) pour meilleur respect des consignes."""
    key_terms = extract_key_terms(question)
    terms_anchor = ""
    if key_terms:
        terms_anchor = f"\nTERMES-CLÉS DE LA QUESTION (à utiliser tels quels, sans les remplacer) : {', '.join(key_terms)}"

    verification_warning = ""
    if is_verification_question(question):
        verification_warning = (
            "\n\n⚠️ ATTENTION : cette question demande de confirmer ou d'infirmer une affirmation. "
            "Je vais fournir une réponse basée sur les documents disponibles, mais assurez-vous de vérifier "
            "les informations pour éviter toute erreur."
        )

    system_msg = f"""Tu es un assistant expert en conformité RGPD. {domaine_context}

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT à partir des DOCUMENTS DE RÉFÉRENCE ci-dessous.
- Si l'information demandée N'EST PAS dans les documents, réponds exactement : "Information non trouvée dans les sources fournies."
- N'INVENTE RIEN : aucun article, aucun organisme, aucune obligation, aucun acronyme qui n'apparaît pas dans les documents.
- INTERDICTION de remplacer un terme de la question par un autre. Si la question mentionne "CSE", ta réponse doit parler du "CSE", pas de la CNIL, du CSPD ou d'un autre organisme.
- Reprends EXACTEMENT les termes de la question dans ta réponse.
- Réponds en français, de façon structurée et professionnelle.
{terms_anchor}
{verification_warning}

FORMAT :
1. Réponse courte et directe
2. Section "Justification à partir des sources :" avec 2-4 puces
3. Si l'info n'est pas trouvée : 'Information non trouvée dans les sources fournies.'

"""

    user_msg = f"""DOCUMENTS DE RÉFÉRENCE :
{contexte}

HISTORIQUE :
{historique_formate}

QUESTION : {question}

RAPPEL : Réponds UNIQUEMENT sur ce qui est demandé ({', '.join(key_terms) if key_terms else question[:50]}). Ne substitue aucun terme. Si les documents ne contiennent pas la réponse, dis-le.

RÉPONSE :"""

    return system_msg, user_msg

def run_ollama_chat(system_msg: str, user_msg: str, num_ctx: int, num_predict: int) -> str:
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        options={"temperature": 0, "num_ctx": num_ctx, "num_predict": num_predict}
    )
    return response['message']['content']

# Contextes par domaine
DOMAINE_CONTEXTES = {
    "sante": """Tu assistes un DPO dans le secteur SANTÉ/MÉDICAL.
    Les données sensibles incluent : données de santé, numéro de sécurité sociale,
    antécédents médicaux, traitements, résultats d'analyses.
    Base légale souvent utilisée : obligation légale, intérêt vital, mission de santé publique.
    Durées de conservation spécifiques : dossier médical 20 ans minimum.""",

    "rh": """Tu assistes un DPO dans les RESSOURCES HUMAINES.
    Les données traitées incluent : nom, prénom, CV, salaire, évaluations,
    coordonnées bancaires, absences, données disciplinaires.
    Base légale : contrat de travail, obligation légale.
    Durées : données paie 5 ans, dossier salarié 5 ans après départ.""",

    "education": """Tu assistes un DPO dans le secteur ÉDUCATION.
    Les données incluent : données d'élèves mineurs, résultats scolaires,
    données parents, données enseignants.
    Attention particulière aux données de mineurs — protection renforcée.""",

    "finance": """Tu assistes un DPO dans le secteur FINANCE/BANQUE.
    Les données incluent : IBAN, revenus, historique transactions,
    données de crédit, données KYC.
    Base légale : obligation légale (LCB-FT), contrat.
    Durées : données bancaires 5 à 10 ans selon type.""",

    "commerce": """Tu assistes un DPO dans le secteur COMMERCE/E-COMMERCE.
    Les données incluent : données clients, historique achats,
    données de paiement, cookies, données de navigation.
    Base légale : consentement, contrat, intérêt légitime.""",

    "juridique": """Tu assistes un DPO dans le secteur JURIDIQUE.
    Les données incluent : données clients, pièces judiciaires,
    données sensibles liées aux affaires.
    Secret professionnel et confidentialité renforcés.""",

    "industrie": """Tu assistes un DPO dans le secteur INDUSTRIEL.
    Les données incluent : données employés, données fournisseurs,
    données de contrôle d'accès, vidéosurveillance.""",

    "general": """Tu assistes un DPO dans une organisation."""
}


def get_vectorstore():
    embeddings = OllamaEmbeddings(
        model=OLLAMA_EMBED_MODEL,
        base_url=OLLAMA_BASE_URL
    )
    return Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings,
        collection_name="rgpd_docs"
    )


def query_agent(question: str, historique: list = [], domaine: str = "general") -> dict:
    if not os.path.exists(CHROMA_DB_PATH):
        return {
            "answer": "Base documentaire non initialisée.",
            "sources": [],
            "source_scores": []
        }

    vectorstore = get_vectorstore()
    ranked_docs = rank_documents(question, vectorstore)
    docs_pertinents = [doc for doc, _ in ranked_docs]

    if not docs_pertinents:
        return {
            "answer": "Aucun document pertinent trouvé. Reformulez votre question.",
            "sources": [],
            "source_scores": []
        }

    contexte = build_llm_context(docs_pertinents)

    sources = []
    source_scores = []
    seen_sources = set()
    for doc, score in ranked_docs:
        source_label = format_source_label(doc)
        if source_label not in seen_sources:
            sources.append(source_label)
            source_scores.append({
                "source": source_label,
                "score": round(score, 5)
            })
            seen_sources.add(source_label)

    domaine_context = DOMAINE_CONTEXTES.get(domaine, DOMAINE_CONTEXTES["general"])

    historique_formate = ""
    if historique:
        for msg in historique[-2:]:  # 2 derniers messages
            role = "Utilisateur" if msg.get("role") == "user" else "Assistant"
            historique_formate += f"{role}: {msg.get('content', '')}\n"

    # Réécriture des questions de vérification en forme neutre
    question_for_llm = neutralize_question(question)
    system_msg, user_msg = build_prompt(question_for_llm, domaine_context, contexte, historique_formate)

    try:
        answer = run_ollama_chat(system_msg, user_msg, num_ctx=1280, num_predict=250)
    except Exception:
        minimal_context = build_llm_context(docs_pertinents[:1])
        _, minimal_user_msg = build_prompt(question, domaine_context, minimal_context, "")
        try:
            answer = run_ollama_chat(system_msg, minimal_user_msg, num_ctx=896, num_predict=180)
        except Exception as e:
            answer = (
                "Erreur : le moteur Ollama a échoué pendant la génération de la réponse. "
                "Les sources ont bien été retrouvées, mais le modèle local est instable sur cette requête. "
                f"Détail technique : {str(e)}"
            )

    # Post-validation anti-hallucination
    answer = validate_answer(question, answer, contexte)

    # FILTRE SOURCES : vider les sources si la reponse indique "non trouve"
    answer_lower = answer.lower()
    not_found_signals = [
        "information non trouv",
        "non trouvee dans les sources",
        "pas dans les documents",
        "aucun document fourni ne mentionne",
        "aucun document ne mentionne",
        "introuvable",
        "reference introuvable",
        "n'apparait pas dans les documents",
    ]
    if any(signal in answer_lower for signal in not_found_signals):
        sources = []
        source_scores = []

    # Verifier aussi la pertinence des sources par rapport aux concepts cles
    if sources:
        relevant_docs = _check_source_relevance(question, docs_pertinents)
        if len(relevant_docs) == 0 and len(docs_pertinents) > 0:
            sources = []
            source_scores = []
            if not any(signal in answer_lower for signal in not_found_signals):
                answer += (
                    "\n\n---\n[!] *Les documents de la base ne contiennent pas "
                    "d'information directe sur ce sujet.*"
                )

    return {
        "answer": answer,
        "sources": sources,
        "source_scores": source_scores
    }

def analyser_traitement(traitement_data: dict) -> dict:
    domaine = traitement_data.get('domaine', 'general')
    question = f"""Analyse ce traitement de données et vérifie sa conformité RGPD.
    Identifie les risques, vérifie la base légale, et donne des recommandations précises.

    Traitement :
    - Nom : {traitement_data.get('nom', 'Non renseigné')}
    - Finalité : {traitement_data.get('finalite', 'Non renseigné')}
    - Base légale : {traitement_data.get('base_legale', 'Non renseigné')}
    - Catégories de données : {traitement_data.get('categories_donnees', 'Non renseigné')}
    - Destinataires : {traitement_data.get('destinataires', 'Non renseigné')}
    - Durée de conservation : {traitement_data.get('duree_conservation', 'Non renseigné')}
    - Transferts hors UE : {traitement_data.get('transferts_hors_ue', 'Non')}
    """
    return query_agent(question, domaine=domaine)