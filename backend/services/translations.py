# backend/services/translations.py

import os
import re
from services.groq_service import call_groq
from database import get_cached_translation, save_translation

def contains_japanese(text: str) -> bool:
    if not text: return False
    # Check for Hiragana, Katakana, or Kanji
    return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))

LABELS = {
    "ko": {
        "education": "학력",
        "experience": "경력",
        "skills": "스킬",
        "projects": "주요 프로젝트",
        "awards": "수상",
        "research": "연구/논문",
        "certificates": "자격증",
        "languages": "언어 능력",
        "current": "재직중",
        "left": "퇴직",
        "fulltime": "정규직",
        "freelance": "프리랜서",
        "individual": "개인",
        "developer": "개발자",
        "summary": "전문 분야 요약",
        "contact": "연락처",
        "visa": "비자 상태",
        "gender": "성별",
        "nationality": "국적",
        "phone": "연락처",
        "email": "이메일",
        "address": "주소",
        "dob": "생년월일",
        "age": "나이",
        "marital_status": "혼인 여부",
        "in": "에서",
        "cover_letter_title": "자기소개서",
        "salutation": "채용 담당자님께,",
        "valediction": "올림,",
        "generated_at": "작성일",
        "page_x_of_y": "페이지 {x} / {y}"
    },
    "ja": {
        "education": "学歴",
        "experience": "職歴",
        "skills": "スキル・技術",
        "projects": "プロジェクト詳細",
        "awards": "受賞",
        "research": "研究・論文",
        "certificates": "免許・資格",
        "languages": "語学",
        "current": "在職中",
        "left": "退職",
        "fulltime": "正社員",
        "freelance": "フリーランス",
        "individual": "個人",
        "developer": "開発者",
        "summary": "自己PR",
        "contact": "連絡先",
        "visa": "在留資格",
        "gender": "性別",
        "nationality": "国籍",
        "phone": "電話",
        "email": "メールアドレス",
        "address": "住所",
        "dob": "生年月日",
        "age": "年齢",
        "marital_status": "配偶者",
        "in": "にて",
        "cover_letter_title": "添え状",
        "salutation": "採用担当者様",
        "valediction": "敬具",
        "generated_at": "作成日",
        "page_x_of_y": "{x} / {y} ページ"
    },
    "en": {
        "education": "Education",
        "experience": "Professional Experience",
        "skills": "Skills & Expertise",
        "projects": "Key Projects",
        "awards": "Awards & Achievements",
        "research": "Research & Academic Work",
        "certificates": "Certifications",
        "languages": "Languages",
        "current": "Current",
        "left": "Resigned",
        "fulltime": "Full-time",
        "freelance": "Freelance",
        "individual": "Individual",
        "developer": "Developer",
        "summary": "Professional Summary",
        "contact": "Contact Information",
        "visa": "Visa",
        "gender": "Gender",
        "nationality": "Nationality",
        "phone": "Phone",
        "email": "Email",
        "address": "Address",
        "dob": "Date of Birth",
        "age": "Age",
        "marital_status": "Marital Status",
        "in": "in",
        "cover_letter_title": "Cover Letter",
        "salutation": "To the Hiring Manager,",
        "valediction": "Sincerely,",
        "generated_at": "Generated at",
        "page_x_of_y": "Page {x} of {y}"
    },
    "zh": {
        "education": "学历",
        "experience": "工作经验",
        "skills": "专业能力",
        "projects": "项目经验",
        "awards": "荣誉奖项",
        "research": "研究成果",
        "certificates": "资质证书",
        "languages": "语言能力",
        "current": "在职",
        "left": "离职",
        "fulltime": "全职",
        "freelance": "自由职业",
        "individual": "个人",
        "developer": "开发者",
        "summary": "个人简介",
        "contact": "联系方式",
        "visa": "在留资格",
        "gender": "性别",
        "nationality": "国籍",
        "phone": "联系电话",
        "email": "电子邮箱",
        "address": "通讯地址",
        "dob": "出生年月",
        "age": "年龄",
        "marital_status": "婚姻状况",
        "in": "于",
        "cover_letter_title": "求职信",
        "salutation": "尊敬的招聘负责人：",
        "valediction": "此致 敬礼",
        "generated_at": "制作日期",
        "page_x_of_y": "第 {x} 页 / 共 {y} 页"
    }
}

TRANSLATION_PROMPT = """
You are a professional resume translator.

Rules:
1. Translate ONLY what is given.
2. Do NOT add or remove any information.
3. Keep all numbers, percentages, and metrics EXACTLY as they are (e.g., 94% stays 94%, 10k+ stays 10k+).
4. Keep company names in English (e.g., 'Logixbuilt Infotech' stays as is).
5. Keep technical terms in English (e.g., 'FastAPI', 'PostgreSQL', 'CNN' stays as is).
6. Translate ONLY natural language sentences.
7. Maintain a professional, sophisticated business tone.
8. Target language: {target_lang}
9. Return ONLY the translation, nothing else. No introductions or explanations.

Text to translate:
{text}
"""

import json
from typing import List, Dict

BATCH_TRANSLATION_PROMPT = """
You are a professional resume translator.

Rules:
1. Translate the following list of items to {target_lang}.
2. Return ONLY a valid JSON array of objects, each containing "index" and "translation".
3. Maintain original meaning, professional tone, and keep technical terms/numbers in English.
4. Return ONLY the JSON, no other text.

Items:
{items_json}
"""

SYNTHESIS_PROMPT = """
You are a professional resume consultant specializing in cultural adaptation for {target_lang_name}.

Task:
Rewrite the following resume snippet (in English) to be more appealing to recruiters in {target_lang_name}.

Rules:
1. DO NOT just translate. REWRITE the content to fit the cultural professional standards of that region.
2. Tone: Highly professional, formal, and achievement-oriented.
3. For Japan: Use business-appropriate Keigo (formal language). Emphasize team collaboration, stability, and specific technical contributions.
4. For China: Emphasize high-impact metrics, certifications, and direct problem-solving results.
5. For South Korea: Use formal tone, emphasize diligence, and specific project roles.
6. Keep all numbers, metrics, and key technical terms (FastAPI, Python, etc.) in English.
7. Length: Keep it similar to the original, but priority is cultural "fit."
8. Return ONLY the rewritten text in {target_lang_name}, nothing else.

Section context: {field_name}
Original English text:
{text}
"""

async def synthesize_text(text: str, target_lang: str, field_name: str = "generic") -> str:
    """Synthesizes and adapts text for a specific culture using Groq."""
    if not text or target_lang == "en":
        return text

    lang_name = {
        "ko": "Korean",
        "ja": "Japanese",
        "zh": "Chinese",
    }.get(target_lang, "English")

    prompt = SYNTHESIS_PROMPT.format(
        target_lang_name=lang_name,
        field_name=field_name,
        text=text
    )
    
    try:
        synthesized = await call_groq(prompt)
        synthesized = synthesized.strip()
        
        # Save to Cache as verified because this was a deliberate synthesis request
        save_translation(field_name, target_lang, text, synthesized, is_verified=True)
        
        return synthesized
    except Exception as e:
        print(f"Synthesis error: {e}")
        return text # Fallback to original English

async def translate_text(text: str, target_lang: str, field_name: str = "generic") -> str:
    """Translates text using Groq with SQLite caching."""
    if not text:
        return text
    
    # Normally skip English, unless the source is Japanese and we want English
    if target_lang == "en" and not contains_japanese(text):
        return text

    # 1. Check Cache
    cached = get_cached_translation(field_name, target_lang, text)
    if cached:
        return cached[0] # translated_text

    # 2. Call AI
    lang_name = {
        "ko": "Korean",
        "ja": "Japanese",
        "zh": "Chinese",
        "de": "German",
        "fr": "French",
        "en": "English"
    }.get(target_lang, "English")

    prompt = TRANSLATION_PROMPT.format(target_lang=lang_name, text=text)
    
    try:
        translated = await call_groq(prompt)
        translated = translated.strip()
        
        # 3. Save to Cache (Mark as unverified initially)
        save_translation(field_name, target_lang, text, translated, is_verified=False)
        
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text # Fallback to original English

async def translate_batch(items: List[Dict[str, str]], target_lang: str) -> List[str]:
    """
    Translates multiple strings in a single API call to avoid rate limits.
    items: List of {"text": "...", "field_name": "..."}
    """
    if not items:
        return []
    
    # Normally skip English, but if all items are already English, we can skip.
    # If any item contains Japanese, we might need to translate even to 'en'.
    if target_lang == "en":
        needs_translation = any(contains_japanese(item["text"]) for item in items)
        if not needs_translation:
            return [item["text"] for item in items]

    results = [None] * len(items)
    to_translate = [] # list of (original_index, item)

    # 1. Check Cache for each
    for i, item in enumerate(items):
        text = item["text"]
        field = item["field_name"]
        if not text:
            results[i] = ""
            continue
            
        cached = get_cached_translation(field, target_lang, text)
        if cached:
            results[i] = cached[0]
        else:
            to_translate.append((i, item))

    if not to_translate:
        return results

    # 2. Call AI in batches of 15 (to be safe with context and RPM)
    lang_name = {"ko": "Korean", "ja": "Japanese", "zh": "Chinese", "en": "English"}.get(target_lang, "English")
    
    # Process in chunks of 15
    for start_idx in range(0, len(to_translate), 15):
        chunk = to_translate[start_idx : start_idx + 15]
        
        chunk_data = [{"index": idx, "text": item["text"]} for idx, item in chunk]
        prompt = BATCH_TRANSLATION_PROMPT.format(
            target_lang=lang_name, 
            items_json=json.dumps(chunk_data, ensure_ascii=False)
        )
        
        try:
            response = await call_groq(prompt)
            # Clean response if AI adds markdown blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            translations = json.loads(response.strip())
            
            for t in translations:
                orig_idx = t["index"]
                translated_text = t["translation"]
                
                # Find the field name for this index
                field_name = next(item["field_name"] for idx, item in chunk if idx == orig_idx)
                orig_text = next(item["text"] for idx, item in chunk if idx == orig_idx)
                
                results[orig_idx] = translated_text
                # 3. Save to Cache
                save_translation(field_name, target_lang, orig_text, translated_text, is_verified=False)
        except Exception as e:
            print(f"Batch translation error for chunk {start_idx}: {e}")
            # Fallback for this chunk
            for idx, item in chunk:
                if results[idx] is None:
                    results[idx] = item["text"]

    # Fill any remaining Nones (shouldn't happen)
    return [r if r is not None else items[i]["text"] for i, r in enumerate(results)]

def get_labels(lang: str):
    """Returns the labels dictionary for the target language."""
    return LABELS.get(lang, LABELS["en"])
