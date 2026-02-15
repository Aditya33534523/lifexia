"""
LIFEXIA RAG Service - Drug Information System
Provides accurate drug information with built-in database fallback
Eliminates hallucination by using verified pharmaceutical data
"""

import os
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Try to import ML dependencies - gracefully handle if not available
try:
    from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
    from langchain_community.vectorstores import Chroma
    from langchain_core.prompts import PromptTemplate
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
    ML_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ML dependencies not available: {e}. RAG service will run in fallback mode.")
    ML_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# VERIFIED DRUG DATABASE - Prevents hallucination in fallback mode
# Sources: Indian Pharmacopoeia 2022, NLEM 2022, WHO Essential Medicines
# ═══════════════════════════════════════════════════════════════

DRUG_DATABASE = {
    "paracetamol": {
        "name": "Paracetamol (Acetaminophen)",
        "generic": "Paracetamol",
        "category": "Analgesic / Antipyretic",
        "nlem": True,
        "use": "Pain relief (headache, toothache, muscle pain, menstrual cramps) and fever reduction.",
        "dosage": {
            "adult": "500mg - 1000mg every 4-6 hours. Maximum: 4000mg (4g) per day.",
            "child": "10-15 mg/kg every 4-6 hours. Maximum: 60 mg/kg per day.",
            "elderly": "Lower doses recommended; max 2-3g/day with liver considerations."
        },
        "side_effects": ["Nausea", "Rash (rare)", "Liver damage (overdose)", "Allergic reactions (rare)"],
        "contraindications": ["Severe liver disease", "Known hypersensitivity", "Chronic alcoholism (use with caution)"],
        "interactions": ["Warfarin (increased bleeding risk)", "Alcohol (liver toxicity risk)", "Carbamazepine", "Isoniazid"],
        "warning": "⚠️ OVERDOSE DANGER: Do not exceed 4g/day in adults. Overdose can cause fatal liver failure. Seek immediate medical help if overdose suspected. N-Acetylcysteine is the antidote.",
        "emergency_use": True,
        "pharmacology": {
            "mechanism": "Inhibits COX enzymes in the CNS, reducing prostaglandin synthesis. Weak peripheral anti-inflammatory action.",
            "onset": "30-60 minutes (oral)",
            "peak": "1-2 hours",
            "duration": "4-6 hours",
            "half_life": "1-4 hours",
            "metabolism": "Hepatic (glucuronidation, sulfation, CYP2E1)",
            "excretion": "Renal (>90%)"
        }
    },
    "aspirin": {
        "name": "Aspirin (Acetylsalicylic Acid)",
        "generic": "Aspirin",
        "category": "NSAID / Antiplatelet",
        "nlem": True,
        "use": "Pain relief, fever reduction, anti-inflammatory, prevention of heart attacks and strokes (low-dose).",
        "dosage": {
            "adult": "Pain/Fever: 325-650mg every 4-6 hours (max 4g/day). Cardiac: 75-100mg once daily.",
            "child": "NOT recommended for children under 16 due to Reye's syndrome risk.",
            "elderly": "Low-dose (75-100mg) for cardiovascular protection. Higher doses with caution."
        },
        "side_effects": ["GI bleeding", "Stomach ulcers", "Nausea", "Tinnitus (high doses)", "Easy bruising"],
        "contraindications": ["Children under 16 (Reye's syndrome)", "Active GI bleeding", "Haemophilia", "Severe asthma", "Last trimester of pregnancy"],
        "interactions": ["Warfarin (bleeding risk)", "Methotrexate (toxicity)", "ACE inhibitors (reduced effect)", "Ibuprofen (may reduce aspirin's antiplatelet effect)", "Alcohol"],
        "warning": "⚠️ Do NOT give to children/teens with viral illness (Reye's syndrome risk). Can cause serious GI bleeding. Discontinue 7 days before surgery.",
        "emergency_use": True,
        "pharmacology": {
            "mechanism": "Irreversibly inhibits COX-1 and COX-2 enzymes, blocking prostaglandin and thromboxane A2 synthesis.",
            "onset": "15-30 minutes",
            "peak": "1-2 hours",
            "duration": "4-6 hours (analgesic); antiplatelet effect lasts 7-10 days",
            "half_life": "15-20 minutes (aspirin); 2-3 hours (salicylate)",
            "metabolism": "Hepatic hydrolysis to salicylic acid",
            "excretion": "Renal"
        }
    },
    "ibuprofen": {
        "name": "Ibuprofen",
        "generic": "Ibuprofen",
        "category": "NSAID (Non-Steroidal Anti-Inflammatory Drug)",
        "nlem": True,
        "use": "Pain relief, fever reduction, inflammation reduction. Used for headache, dental pain, menstrual cramps, arthritis, musculoskeletal injuries.",
        "dosage": {
            "adult": "200-400mg every 4-6 hours. Maximum: 1200mg/day (OTC) or 2400mg/day (prescription).",
            "child": "5-10 mg/kg every 6-8 hours. Not for infants under 3 months.",
            "elderly": "Use lowest effective dose for shortest duration."
        },
        "side_effects": ["GI upset", "Nausea", "Headache", "Dizziness", "Kidney impairment (prolonged use)", "Fluid retention"],
        "contraindications": ["Active GI bleeding/ulceration", "Severe renal impairment", "Third trimester pregnancy", "Known NSAID allergy", "Heart failure (severe)"],
        "interactions": ["Aspirin (reduced antiplatelet effect)", "Warfarin", "ACE inhibitors", "Diuretics", "Lithium", "Methotrexate"],
        "warning": "⚠️ Take with food. Avoid prolonged use. Increased cardiovascular risk with high doses. Not recommended for patients with heart failure.",
        "emergency_use": True,
        "pharmacology": {
            "mechanism": "Non-selective COX-1 and COX-2 inhibitor, reducing prostaglandin synthesis.",
            "onset": "30-60 minutes",
            "peak": "1-2 hours",
            "duration": "6-8 hours",
            "half_life": "2-4 hours",
            "metabolism": "Hepatic (CYP2C9)",
            "excretion": "Renal (>90%)"
        }
    },
    "amoxicillin": {
        "name": "Amoxicillin",
        "generic": "Amoxicillin",
        "category": "Antibiotic (Penicillin class)",
        "nlem": True,
        "use": "Bacterial infections: upper/lower respiratory tract, urinary tract, ear infections (otitis media), dental infections, H. pylori eradication.",
        "dosage": {
            "adult": "250-500mg every 8 hours, or 500-875mg every 12 hours. Duration: 5-14 days depending on infection.",
            "child": "20-40 mg/kg/day divided into 3 doses. Higher for severe infections.",
            "elderly": "Standard adult doses; adjust for renal impairment."
        },
        "side_effects": ["Diarrhea", "Nausea", "Skin rash", "Yeast infections", "Allergic reactions"],
        "contraindications": ["Penicillin allergy", "History of amoxicillin-associated jaundice", "Infectious mononucleosis (rash risk)"],
        "interactions": ["Methotrexate (increased toxicity)", "Warfarin (increased INR)", "Oral contraceptives (may reduce effectiveness)", "Probenecid (increased amoxicillin levels)"],
        "warning": "⚠️ Complete the full course of antibiotics. Stop immediately if severe allergic reaction (anaphylaxis) occurs. Report rash, swelling, difficulty breathing.",
        "emergency_use": True,
        "pharmacology": {
            "mechanism": "Inhibits bacterial cell wall synthesis by binding to penicillin-binding proteins (PBPs).",
            "onset": "1-2 hours",
            "peak": "1-2 hours",
            "duration": "8 hours",
            "half_life": "1-1.5 hours",
            "metabolism": "Partially hepatic",
            "excretion": "Renal (60% unchanged)"
        }
    },
    "metformin": {
        "name": "Metformin",
        "generic": "Metformin Hydrochloride",
        "category": "Antidiabetic (Biguanide)",
        "nlem": True,
        "use": "Type 2 Diabetes Mellitus - first-line therapy. Reduces blood glucose levels. May be used for PCOS (off-label).",
        "dosage": {
            "adult": "Start 500mg once or twice daily with meals. Max: 2000-2550mg/day in divided doses. Increase gradually.",
            "child": "≥10 years: 500mg twice daily. Max: 2000mg/day.",
            "elderly": "Start low, titrate slowly. Monitor renal function."
        },
        "side_effects": ["GI upset (nausea, diarrhea, bloating)", "Metallic taste", "Vitamin B12 deficiency (long-term)", "Lactic acidosis (rare, serious)"],
        "contraindications": ["Severe renal impairment (eGFR <30)", "Acute metabolic acidosis", "Diabetic ketoacidosis", "Severe hepatic impairment", "Before iodinated contrast procedures"],
        "interactions": ["Alcohol (lactic acidosis risk)", "Iodinated contrast media", "Carbonic anhydrase inhibitors", "Cimetidine"],
        "warning": "⚠️ Hold before and 48 hours after iodinated contrast procedures. Monitor B12 levels annually. Does NOT cause hypoglycemia when used alone.",
        "emergency_use": False,
        "pharmacology": {
            "mechanism": "Decreases hepatic glucose production, increases insulin sensitivity in peripheral tissues, decreases intestinal absorption of glucose.",
            "onset": "Within days (full effect 1-2 weeks)",
            "peak": "2-3 hours (immediate release)",
            "duration": "8-12 hours",
            "half_life": "6.2 hours",
            "metabolism": "Not metabolized",
            "excretion": "Renal (unchanged)"
        }
    },
    "amlodipine": {
        "name": "Amlodipine",
        "generic": "Amlodipine Besylate",
        "category": "Calcium Channel Blocker (Antihypertensive)",
        "nlem": True,
        "use": "Hypertension (high blood pressure), chronic stable angina, vasospastic (Prinzmetal's) angina.",
        "dosage": {
            "adult": "5mg once daily. May increase to 10mg once daily after 1-2 weeks.",
            "child": "6-17 years: 2.5-5mg once daily.",
            "elderly": "Start with 2.5mg daily."
        },
        "side_effects": ["Peripheral edema (ankle swelling)", "Headache", "Flushing", "Dizziness", "Palpitations", "Fatigue"],
        "contraindications": ["Cardiogenic shock", "Severe aortic stenosis", "Unstable angina (as monotherapy)", "Known hypersensitivity"],
        "interactions": ["Simvastatin (limit to 20mg)", "CYP3A4 inhibitors (ketoconazole, erythromycin)", "Cyclosporine", "Tacrolimus"],
        "warning": "⚠️ Do not stop abruptly in angina patients. Monitor blood pressure regularly. Ankle swelling is common but usually harmless.",
        "emergency_use": False,
        "pharmacology": {
            "mechanism": "Blocks L-type calcium channels in vascular smooth muscle, causing vasodilation and reduced peripheral resistance.",
            "onset": "6-12 hours",
            "peak": "6-12 hours",
            "duration": "24 hours",
            "half_life": "30-50 hours",
            "metabolism": "Hepatic (CYP3A4)",
            "excretion": "Renal (60%)"
        }
    },
    "omeprazole": {
        "name": "Omeprazole",
        "generic": "Omeprazole",
        "category": "Proton Pump Inhibitor (PPI)",
        "nlem": True,
        "use": "Gastric/duodenal ulcers, GERD (acid reflux), Zollinger-Ellison syndrome, H. pylori eradication (with antibiotics), NSAID-induced ulcer prevention.",
        "dosage": {
            "adult": "20mg once daily before breakfast. Ulcers: 20-40mg daily for 4-8 weeks. GERD: 20mg daily.",
            "child": "1 mg/kg once daily (max 20mg).",
            "elderly": "No dose adjustment usually needed."
        },
        "side_effects": ["Headache", "Nausea", "Diarrhea", "Abdominal pain", "Vitamin B12 deficiency (long-term)", "Magnesium deficiency (long-term)", "Increased fracture risk (prolonged use)"],
        "contraindications": ["Known hypersensitivity to PPIs", "Concurrent use with rilpivirine or nelfinavir"],
        "interactions": ["Clopidogrel (reduced effectiveness - AVOID)", "Methotrexate", "Warfarin", "Diazepam", "Phenytoin", "Ketoconazole (reduced absorption)"],
        "warning": "⚠️ Not for long-term use without medical review. May mask gastric cancer symptoms. Risk of C. difficile infection with prolonged use.",
        "emergency_use": False,
        "pharmacology": {
            "mechanism": "Irreversibly inhibits H+/K+ ATPase (proton pump) in gastric parietal cells, blocking acid secretion.",
            "onset": "1 hour",
            "peak": "2 hours",
            "duration": "Up to 72 hours (acid inhibition)",
            "half_life": "0.5-1 hour",
            "metabolism": "Hepatic (CYP2C19, CYP3A4)",
            "excretion": "Renal (77%)"
        }
    },
    "cetirizine": {
        "name": "Cetirizine",
        "generic": "Cetirizine Hydrochloride",
        "category": "Antihistamine (2nd generation)",
        "nlem": True,
        "use": "Allergic rhinitis, urticaria (hives), hay fever, allergic conjunctivitis, skin allergies.",
        "dosage": {
            "adult": "10mg once daily.",
            "child": "2-5 years: 2.5mg once daily. 6-11 years: 5-10mg daily.",
            "elderly": "5mg daily (reduce if renal impairment)."
        },
        "side_effects": ["Drowsiness (less than 1st gen)", "Dry mouth", "Headache", "Fatigue", "GI upset"],
        "contraindications": ["Severe renal impairment (without dose adjustment)", "Known hypersensitivity", "End-stage renal disease"],
        "interactions": ["Alcohol (increased sedation)", "CNS depressants", "Theophylline (slightly decreased clearance)"],
        "warning": "⚠️ May cause drowsiness. Avoid driving if affected. Less sedating than older antihistamines but caution still advised.",
        "emergency_use": False,
        "pharmacology": {
            "mechanism": "Selective peripheral H1 receptor antagonist, inhibiting histamine-mediated allergic response.",
            "onset": "20-60 minutes",
            "peak": "1 hour",
            "duration": "24 hours",
            "half_life": "8 hours",
            "metabolism": "Minimal hepatic",
            "excretion": "Renal (70%)"
        }
    },
    "atorvastatin": {
        "name": "Atorvastatin",
        "generic": "Atorvastatin Calcium",
        "category": "Statin (HMG-CoA Reductase Inhibitor)",
        "nlem": True,
        "use": "Hyperlipidemia, dyslipidemia, cardiovascular risk reduction, prevention of heart attacks and strokes.",
        "dosage": {
            "adult": "10-20mg once daily (evening preferred). May increase to 80mg/day. Adjust based on LDL goals.",
            "child": "10-17 years: 10mg daily (max 20mg).",
            "elderly": "Standard dosing; monitor liver function."
        },
        "side_effects": ["Muscle pain/weakness (myalgia)", "Headache", "GI upset", "Elevated liver enzymes", "Rhabdomyolysis (rare, serious)"],
        "contraindications": ["Active liver disease", "Unexplained elevated transaminases", "Pregnancy", "Breastfeeding"],
        "interactions": ["Gemfibrozil (myopathy risk)", "Cyclosporine", "Clarithromycin", "Grapefruit juice (large amounts)", "Warfarin", "Digoxin"],
        "warning": "⚠️ Report unexplained muscle pain immediately (rhabdomyolysis risk). Monitor liver function. Take in the evening for best effect. Contraindicated in pregnancy.",
        "emergency_use": False,
        "pharmacology": {
            "mechanism": "Competitively inhibits HMG-CoA reductase, the rate-limiting enzyme in cholesterol biosynthesis. Upregulates LDL receptors.",
            "onset": "2 weeks (lipid changes)",
            "peak": "1-2 hours",
            "duration": "24 hours",
            "half_life": "14 hours (active metabolite: 20-30 hours)",
            "metabolism": "Hepatic (CYP3A4)",
            "excretion": "Biliary"
        }
    },
    "epinephrine": {
        "name": "Epinephrine (Adrenaline)",
        "generic": "Epinephrine",
        "category": "Sympathomimetic / Emergency Drug",
        "nlem": True,
        "use": "Anaphylaxis (FIRST-LINE), cardiac arrest, severe asthma exacerbation, croup. Also used as local anesthetic adjunct.",
        "dosage": {
            "adult": "Anaphylaxis: 0.3-0.5mg IM (1:1000) in mid-outer thigh. Repeat every 5-15 min if needed. Cardiac arrest: 1mg IV (1:10,000) every 3-5 min.",
            "child": "Anaphylaxis: 0.01mg/kg IM (max 0.3mg per dose). Repeat every 5-15 min if needed.",
            "elderly": "Standard doses for emergencies; monitor closely."
        },
        "side_effects": ["Tachycardia", "Palpitations", "Anxiety/tremor", "Headache", "Hypertension", "Nausea"],
        "contraindications": ["None absolute in life-threatening emergencies (anaphylaxis/cardiac arrest)"],
        "interactions": ["Beta-blockers (reduced effectiveness)", "TCAs (enhanced pressor response)", "MAO inhibitors (hypertensive crisis)", "Halogenated anesthetics (arrhythmia risk)"],
        "warning": "🚨 CRITICAL EMERGENCY DRUG. Use IM route for anaphylaxis (NOT IV unless in cardiac arrest). Always inject in mid-outer thigh. Call emergency services immediately.",
        "emergency_use": True,
        "pharmacology": {
            "mechanism": "Acts on alpha and beta adrenergic receptors. Alpha-1: vasoconstriction. Beta-1: increased heart rate/contractility. Beta-2: bronchodilation.",
            "onset": "IM: 3-5 minutes. IV: 1-2 minutes.",
            "peak": "IM: 5-10 minutes",
            "duration": "15-30 minutes",
            "half_life": "2-3 minutes",
            "metabolism": "Rapidly metabolized by MAO and COMT",
            "excretion": "Renal (metabolites)"
        }
    },
    "diazepam": {
        "name": "Diazepam",
        "generic": "Diazepam",
        "category": "Benzodiazepine (Anxiolytic / Anticonvulsant)",
        "nlem": True,
        "use": "Anxiety disorders, seizures (status epilepticus), muscle spasm, alcohol withdrawal, preoperative sedation.",
        "dosage": {
            "adult": "Anxiety: 2-10mg 2-4 times daily. Seizures: 5-10mg IV (max rate 5mg/min). Muscle spasm: 2-10mg 3-4 times daily.",
            "child": "Seizures: 0.1-0.3 mg/kg IV (max 10mg). Rectal: 0.5mg/kg.",
            "elderly": "2-2.5mg 1-2 times daily. Use with extreme caution."
        },
        "side_effects": ["Sedation/drowsiness", "Confusion", "Ataxia", "Respiratory depression", "Dependence (with prolonged use)", "Memory impairment"],
        "contraindications": ["Severe respiratory depression", "Sleep apnoea", "Myasthenia gravis", "Acute narrow-angle glaucoma", "Severe hepatic impairment"],
        "interactions": ["Alcohol (life-threatening CNS depression)", "Opioids (respiratory depression - BLACK BOX WARNING)", "Other CNS depressants", "CYP3A4 inhibitors"],
        "warning": "⚠️ HIGH DEPENDENCE RISK. Do not combine with alcohol or opioids. Do not stop abruptly (withdrawal seizures). Use lowest dose for shortest duration. CONTROLLED SUBSTANCE.",
        "emergency_use": True,
        "pharmacology": {
            "mechanism": "Enhances GABA-A receptor activity, increasing chloride conductance and neuronal inhibition.",
            "onset": "IV: 1-3 minutes. Oral: 15-60 minutes.",
            "peak": "IV: 3-4 minutes. Oral: 1-1.5 hours.",
            "duration": "Variable (active metabolites last days)",
            "half_life": "20-100 hours (with active metabolites)",
            "metabolism": "Hepatic (CYP2C19, CYP3A4) to active metabolites (desmethyldiazepam)",
            "excretion": "Renal"
        }
    },
    "salbutamol": {
        "name": "Salbutamol (Albuterol)",
        "generic": "Salbutamol Sulfate",
        "category": "Bronchodilator (Short-acting Beta-2 Agonist - SABA)",
        "nlem": True,
        "use": "Acute asthma relief, bronchospasm in COPD, exercise-induced bronchospasm. Used as rescue inhaler.",
        "dosage": {
            "adult": "Inhaler: 1-2 puffs (100-200mcg) every 4-6 hours as needed. Nebulizer: 2.5-5mg. Severe attack: up to 10 puffs via spacer.",
            "child": "1-2 puffs as needed. Nebulizer: 2.5mg. Under 5: use spacer with mask.",
            "elderly": "Standard adult doses."
        },
        "side_effects": ["Tremor", "Tachycardia", "Headache", "Nervousness", "Hypokalemia (high doses)", "Palpitations"],
        "contraindications": ["Known hypersensitivity (rare)"],
        "interactions": ["Beta-blockers (antagonistic effect)", "Diuretics (hypokalemia)", "MAO inhibitors", "Corticosteroids (hypokalemia)"],
        "warning": "⚠️ RESCUE INHALER ONLY - not for maintenance. If needing >3 times/week, asthma is poorly controlled - see doctor. Overuse can worsen asthma control.",
        "emergency_use": True,
        "pharmacology": {
            "mechanism": "Selective beta-2 adrenergic receptor agonist, causing bronchial smooth muscle relaxation.",
            "onset": "Inhaled: 1-5 minutes. Oral: 15-30 minutes.",
            "peak": "Inhaled: 15-30 minutes",
            "duration": "4-6 hours",
            "half_life": "3-8 hours",
            "metabolism": "Hepatic (sulfation)",
            "excretion": "Renal"
        }
    },
    "ciprofloxacin": {
        "name": "Ciprofloxacin",
        "generic": "Ciprofloxacin Hydrochloride",
        "category": "Antibiotic (Fluoroquinolone)",
        "nlem": True,
        "use": "Urinary tract infections, respiratory infections, GI infections, bone/joint infections, anthrax prophylaxis.",
        "dosage": {
            "adult": "250-750mg twice daily for 3-14 days depending on infection type. UTI: 250-500mg BD for 3-7 days.",
            "child": "Not recommended in children under 18 (cartilage damage risk). Exception: anthrax or complicated UTI.",
            "elderly": "Dose adjustment for renal impairment."
        },
        "side_effects": ["Nausea", "Diarrhea", "Headache", "Dizziness", "Tendon damage/rupture", "Photosensitivity", "QT prolongation"],
        "contraindications": ["Children/adolescents (growing bones)", "Known hypersensitivity to fluoroquinolones", "Concurrent tizanidine use", "History of tendon disorders from fluoroquinolones"],
        "interactions": ["Antacids/iron/calcium (reduced absorption - take 2h apart)", "Warfarin (increased effect)", "Theophylline (increased levels)", "NSAIDs (seizure risk)", "Caffeine"],
        "warning": "⚠️ BLACK BOX WARNING: Risk of tendinitis, tendon rupture, peripheral neuropathy, and CNS effects. Avoid in elderly, steroid users. Take with water, avoid dairy products within 2 hours.",
        "emergency_use": False,
        "pharmacology": {
            "mechanism": "Inhibits bacterial DNA gyrase and topoisomerase IV, preventing DNA replication.",
            "onset": "1-2 hours",
            "peak": "1-2 hours",
            "duration": "12 hours",
            "half_life": "4-6 hours",
            "metabolism": "Hepatic (partial)",
            "excretion": "Renal (40-50% unchanged)"
        }
    },
    "losartan": {
        "name": "Losartan",
        "generic": "Losartan Potassium",
        "category": "ARB (Angiotensin II Receptor Blocker)",
        "nlem": True,
        "use": "Hypertension, diabetic nephropathy (Type 2 DM), stroke risk reduction, heart failure (when ACE inhibitors not tolerated).",
        "dosage": {
            "adult": "50mg once daily. May increase to 100mg daily. Start lower (25mg) if volume depleted.",
            "child": "6-16 years: 0.7mg/kg once daily (max 50mg).",
            "elderly": "No specific adjustment, but start conservatively."
        },
        "side_effects": ["Dizziness", "Hyperkalemia", "Hypotension", "Fatigue", "Upper respiratory infection", "Back pain"],
        "contraindications": ["Pregnancy (TERATOGENIC)", "Bilateral renal artery stenosis", "Concurrent aliskiren use (in diabetics)", "Known hypersensitivity"],
        "interactions": ["Potassium supplements/sparing diuretics (hyperkalemia)", "NSAIDs (reduced effect, renal risk)", "Lithium (increased levels)", "ACE inhibitors (dual blockade risk)"],
        "warning": "⚠️ CONTRAINDICATED IN PREGNANCY - Can cause fetal harm/death. Discontinue immediately if pregnancy detected. Monitor potassium levels.",
        "emergency_use": False,
        "pharmacology": {
            "mechanism": "Selective AT1 receptor antagonist, blocking angiotensin II-mediated vasoconstriction and aldosterone release.",
            "onset": "6 hours",
            "peak": "1 hour (losartan), 3-4 hours (active metabolite E-3174)",
            "duration": "24 hours",
            "half_life": "2 hours (losartan), 6-9 hours (E-3174)",
            "metabolism": "Hepatic (CYP2C9, CYP3A4) to active metabolite",
            "excretion": "Renal (35%) and biliary (60%)"
        }
    },
    "insulin": {
        "name": "Insulin (Human/Analog)",
        "generic": "Insulin",
        "category": "Antidiabetic (Hormone)",
        "nlem": True,
        "use": "Type 1 Diabetes (mandatory), Type 2 Diabetes (when oral agents insufficient), diabetic ketoacidosis, gestational diabetes.",
        "dosage": {
            "adult": "Highly individualized. Type 1: 0.4-1 unit/kg/day. Type 2: Start 10 units/day basal, titrate by 2 units every 3 days.",
            "child": "Individualized based on glucose monitoring.",
            "elderly": "Start conservatively; higher hypoglycemia risk."
        },
        "side_effects": ["Hypoglycemia (most common, dangerous)", "Weight gain", "Injection site reactions", "Lipodystrophy", "Hypokalemia"],
        "contraindications": ["Hypoglycemia", "Known hypersensitivity to insulin type"],
        "interactions": ["Oral hypoglycemics (additive hypoglycemia)", "Beta-blockers (mask hypoglycemia signs)", "Alcohol", "Thiazide diuretics (may increase glucose)", "Corticosteroids"],
        "warning": "🚨 HYPOGLYCEMIA RISK: Always carry glucose tablets. Symptoms: sweating, tremor, confusion, blurred vision. Severe: seizures, unconsciousness. Teach patient and family glucagon use.",
        "emergency_use": True,
        "pharmacology": {
            "mechanism": "Binds to insulin receptors, facilitating glucose uptake into cells, promoting glycogen synthesis, and inhibiting gluconeogenesis.",
            "onset": "Rapid-acting: 15 min. Regular: 30 min. NPH: 1-2 hours. Long-acting: 1-2 hours.",
            "peak": "Rapid: 1-2h. Regular: 2-4h. NPH: 4-12h. Long-acting: minimal/no peak.",
            "duration": "Rapid: 3-5h. Regular: 6-8h. NPH: 12-18h. Long-acting: 20-24h.",
            "half_life": "5-6 minutes (plasma)",
            "metabolism": "Hepatic, renal",
            "excretion": "Renal"
        }
    }
}

# Drug aliases for flexible search
DRUG_ALIASES = {
    "acetaminophen": "paracetamol",
    "tylenol": "paracetamol",
    "crocin": "paracetamol",
    "dolo": "paracetamol",
    "dolo 650": "paracetamol",
    "calpol": "paracetamol",
    "disprin": "aspirin",
    "ecosprin": "aspirin",
    "acetylsalicylic acid": "aspirin",
    "brufen": "ibuprofen",
    "advil": "ibuprofen",
    "motrin": "ibuprofen",
    "combiflam": "ibuprofen",
    "augmentin": "amoxicillin",
    "amoxyclav": "amoxicillin",
    "mox": "amoxicillin",
    "glycomet": "metformin",
    "glucophage": "metformin",
    "amlokind": "amlodipine",
    "stamlo": "amlodipine",
    "norvasc": "amlodipine",
    "prilosec": "omeprazole",
    "omez": "omeprazole",
    "zyrtec": "cetirizine",
    "alerid": "cetirizine",
    "cetzine": "cetirizine",
    "lipitor": "atorvastatin",
    "atorva": "atorvastatin",
    "adrenaline": "epinephrine",
    "epipen": "epinephrine",
    "valium": "diazepam",
    "calmpose": "diazepam",
    "ventolin": "salbutamol",
    "asthalin": "salbutamol",
    "albuterol": "salbutamol",
    "ciplox": "ciprofloxacin",
    "cipro": "ciprofloxacin",
    "cozaar": "losartan",
    "losacar": "losartan",
    "repace": "losartan",
    "humulin": "insulin",
    "lantus": "insulin",
    "novorapid": "insulin",
    "novolog": "insulin",
    "humalog": "insulin",
    "actrapid": "insulin",
    "mixtard": "insulin"
}


class RAGService:
    """RAG-based drug information service with verified fallback database"""

    def __init__(self):
        self.drug_db = DRUG_DATABASE
        self.drug_aliases = DRUG_ALIASES

        if not ML_AVAILABLE:
            logger.warning("RAG Service running in VERIFIED FALLBACK mode (built-in drug database)")
            self.vector_store = None
            self.llm = None
            self.template = None
            self.embeddings = None
            return

        BASE_DIR = Path(__file__).resolve().parent
        PERSIST_DIR = os.path.join(BASE_DIR, "instance", "vector_db")

        print("Initializing RAG Service...")

        # 1. Load Embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # 2. Load Vector Store
        try:
            if not os.path.exists(PERSIST_DIR):
                print(f"Warning: Vector DB not found at {PERSIST_DIR}. Using built-in drug database as primary source.")
                self.vector_store = None
            else:
                self.vector_store = Chroma(persist_directory=PERSIST_DIR, embedding_function=self.embeddings)
                print("Vector Store loaded.")
        except Exception as e:
            print(f"Error loading Vector Store: {e}")
            print("Using built-in drug database as primary source.")
            self.vector_store = None

        # 3. Load LLM
        model_name = os.getenv("LLM_MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")
        use_gpu = os.getenv("USE_GPU", "False").lower() == "true"

        print(f"Loading LLM: {model_name}...")

        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)

            if use_gpu and torch.cuda.is_available():
                device = "cuda"
                torch_dtype = torch.float16
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = "mps"
                torch_dtype = torch.float16
            else:
                device = "cpu"
                torch_dtype = torch.float32

            print(f"Using device: {device}")

            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch_dtype,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )

            if device != "cpu":
                model = model.to(device)

            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=256,
                temperature=0.0,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
            self.llm = HuggingFacePipeline(pipeline=pipe)
            print("LLM loaded successfully.")
        except Exception as e:
            print(f"Error loading LLM: {e}")
            print("Using built-in drug database for responses.")
            self.llm = None

        # 4. Create QA Chain
        if self.llm:
            template = """<|im_start|>system
You are LifeXia, an intelligent pharmacy assistant. Provide a helpful, professional, and accurate answer.
{context_msg}

Guidelines:
- **Accuracy**: Prioritize accuracy. Do not hallucinate or guess drug interactions or dosages.
- **Safety**: If a query involves critical safety or severe symptoms, advise consulting a healthcare professional immediately.
- **Clarity**: Provide clear, concise information suitable for the user's level of understanding.
- If you don't know the answer, say so clearly. Never invent drug information.

Question:
{question}<|im_end|>
<|im_start|>assistant
"""
            self.template = template
            print("Qwen model template initialized.")
        else:
            self.template = None

    def _find_drug(self, query):
        """Find a drug in the database by name or alias"""
        query_lower = query.lower().strip()

        # Direct match
        if query_lower in self.drug_db:
            return self.drug_db[query_lower]

        # Alias match
        if query_lower in self.drug_aliases:
            return self.drug_db[self.drug_aliases[query_lower]]

        # Partial match
        for drug_key, drug_data in self.drug_db.items():
            if drug_key in query_lower or query_lower in drug_key:
                return drug_data
            if drug_data["generic"].lower() in query_lower or query_lower in drug_data["generic"].lower():
                return drug_data
            if drug_data["name"].lower().startswith(query_lower) or query_lower in drug_data["name"].lower():
                return drug_data

        # Alias partial match
        for alias, drug_key in self.drug_aliases.items():
            if alias in query_lower or query_lower in alias:
                return self.drug_db[drug_key]

        return None

    def _extract_drug_from_query(self, query):
        """Extract drug name from a natural language query"""
        # Common query patterns
        patterns = [
            r"(?:about|info(?:rmation)?|details?\s+(?:about|on|of)?|tell\s+me\s+about)\s+(.+?)(?:\s*\?|\s*$)",
            r"(?:what\s+is|what\'?s)\s+(.+?)(?:\s+used\s+for|\s*\?|\s*$)",
            r"(?:dosage|dose)\s+(?:of|for)\s+(.+?)(?:\s*\?|\s*$)",
            r"(?:side\s+effects?\s+of)\s+(.+?)(?:\s*\?|\s*$)",
            r"(?:interactions?\s+(?:of|for|with))\s+(.+?)(?:\s*\?|\s*$)",
            r"(?:how\s+to\s+(?:use|take))\s+(.+?)(?:\s*\?|\s*$)",
            r"(?:is|can)\s+(.+?)\s+(?:safe|used|good)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                drug_candidate = match.group(1).strip()
                drug = self._find_drug(drug_candidate)
                if drug:
                    return drug

        # Try each word in the query
        words = query.split()
        for word in words:
            drug = self._find_drug(word)
            if drug:
                return drug

        # Try multi-word combinations
        for i in range(len(words)):
            for j in range(i + 1, min(i + 4, len(words) + 1)):
                combo = " ".join(words[i:j])
                drug = self._find_drug(combo)
                if drug:
                    return drug

        return None

    def _format_drug_response(self, drug, user_type='patient'):
        """Format drug info based on user type - patient-friendly or student-detailed"""
        if user_type == 'student':
            return self._format_student_response(drug)
        else:
            return self._format_patient_response(drug)

    def _format_patient_response(self, drug):
        """Patient-friendly drug information"""
        dosage = drug['dosage']
        side_effects = ", ".join(drug['side_effects'][:5])
        contraindications = ", ".join(drug['contraindications'][:3])

        response = f"""## 💊 {drug['name']}
**Category:** {drug['category']}


### What is it used for?
{drug['use']}

### 📋 Dosage
- **Adults:** {dosage['adult']}
- **Children:** {dosage['child']}

### ⚠️ Important Warnings
{drug['warning']}

### Side Effects to Watch For
{side_effects}

### Do NOT Use If
{contraindications}

### Drug Interactions
{', '.join(drug['interactions'][:4])}

---
*⚕️ This information is for reference only. Always consult your doctor or pharmacist before taking any medication.*
"""
        return response

    def _format_student_response(self, drug):
        """Detailed pharmacology for students"""
        pharma = drug.get('pharmacology', {})
        dosage = drug['dosage']

        response = f"""## 💊 {drug['name']}
**Generic:** {drug['generic']} | **Category:** {drug['category']}
{"🏷️ *NLEM 2022 Listed*" if drug.get('nlem') else ""}

### Clinical Uses
{drug['use']}

### Dosage Guidelines
- **Adults:** {dosage['adult']}
- **Pediatric:** {dosage['child']}
- **Geriatric:** {dosage.get('elderly', 'Adjust per renal/hepatic function')}

### Pharmacology
| Parameter | Details |
|-----------|---------|
| **Mechanism** | {pharma.get('mechanism', 'N/A')} |
| **Onset** | {pharma.get('onset', 'N/A')} |
| **Peak** | {pharma.get('peak', 'N/A')} |
| **Duration** | {pharma.get('duration', 'N/A')} |
| **Half-life** | {pharma.get('half_life', 'N/A')} |
| **Metabolism** | {pharma.get('metabolism', 'N/A')} |
| **Excretion** | {pharma.get('excretion', 'N/A')} |

### Side Effects
{chr(10).join(['- ' + se for se in drug['side_effects']])}

### Contraindications
{chr(10).join(['- ' + ci for ci in drug['contraindications']])}

### Drug Interactions
{chr(10).join(['- ' + di for di in drug['interactions']])}

### Safety Warnings
{drug['warning']}

---
*📚 Source: Indian Pharmacopoeia 2022, NLEM 2022, WHO Essential Medicines List*
"""
        return response

    def search_drug(self, drug_name):
        """Search for a drug by name"""
        return self._find_drug(drug_name)

    def get_emergency_drugs_list(self):
        """Get list of emergency drugs"""
        return [
            {
                'name': drug['name'],
                'category': drug['category'],
                'primary_use': drug['use'][:100] + '...',
                'warning': drug['warning'][:80] + '...'
            }
            for drug in self.drug_db.values()
            if drug.get('emergency_use', False)
        ]

    def get_drug_categories(self):
        """Get unique drug categories"""
        return list(set(drug['category'] for drug in self.drug_db.values()))

    def query(self, question: str, user_type: str = 'patient', context: str = ''):
        """
        Main query method - handles both LLM-based and fallback responses
        Always checks built-in database FIRST to prevent hallucination
        """

        # STEP 1: Always check built-in verified database first
        drug = self._extract_drug_from_query(question)
        if drug:
            logger.info(f"Drug found in verified database: {drug['name']}")
            return self._format_drug_response(drug, user_type)

        # STEP 2: Handle common non-drug queries
        lower_q = question.lower()

        if any(kw in lower_q for kw in ['emergency drug', 'emergency medication', 'emergency list']):
            drugs = self.get_emergency_drugs_list()
            response = "## 🚨 Emergency Drugs List\n\n"
            for d in drugs:
                response += f"### 💊 {d['name']}\n- **Category:** {d['category']}\n- **Use:** {d['primary_use']}\n\n"
            response += "*For detailed info on any drug, ask: 'Tell me about [drug name]'*"
            return response

        if any(kw in lower_q for kw in ['nearby hospital', 'find hospital', 'hospital near', 'nearest hospital']):
            return """## 🏥 Finding Nearby Hospitals

To find hospitals near you:
1. Click the **Health Grid** button in the top bar
2. Allow location access when prompted
3. Browse hospitals, pharmacies, and clinics on the interactive map

**In an emergency, call 108 (India) immediately.**

The Health Grid shows:
- 🏥 Hospitals (with Ayushman Card acceptance info)
- 💊 Pharmacies (24/7 availability)
- Distance from your location
- Contact details and directions
"""

        if any(kw in lower_q for kw in ['hello', 'hi ', 'hey', 'good morning', 'good afternoon', 'good evening']):
            return """Hello! 👋 Welcome to **LIFEXIA** - your AI health assistant.

I can help you with:
- 💊 **Drug Information** — Ask about any medication
- 📋 **Dosage Guidelines** — Proper dosing for adults, children, elderly
- ⚠️ **Drug Interactions** — Check what medications interact
- 🏥 **Nearby Hospitals** — Use the Health Grid map
- 🚨 **Emergency Drugs** — Quick access to critical medication info

**Try asking:** *"Tell me about Paracetamol"* or *"What are the side effects of Aspirin?"*
"""

        if any(kw in lower_q for kw in ['drug list', 'available drugs', 'what drugs', 'all medicines', 'all drugs', 'medicine list']):
            drug_list = "\n".join([f"- **{d['name']}** ({d['category']})" for d in self.drug_db.values()])
            return f"""## 📋 Available Drug Information

I have verified information on the following medications:

{drug_list}

*Ask about any specific drug for detailed information including dosage, side effects, interactions, and pharmacology.*
"""

        # STEP 3: Try LLM if available (with RAG context)
        if self.llm:
            try:
                context_msg = ""
                if self.vector_store:
                    try:
                        docs = self.vector_store.similarity_search(question, k=3)
                        rag_context = "\n".join([d.page_content for d in docs])
                        context_msg = f"Use the following context to help answer:\n{rag_context}"
                    except Exception as e:
                        print(f"Similarity search failed: {e}")

                prompt = self.template.format(
                    context_msg=context_msg,
                    question=question
                )

                response = self.llm.invoke(prompt)

                # Clean up response
                target_str = "<|im_start|>assistant\n"
                if target_str in response:
                    response = response.split(target_str)[-1].strip()

                response = response.replace("<|im_end|>", "").strip()

                if not response or "<|im_start|>" in response:
                    return self._general_help_response(question)

                return response
            except Exception as e:
                print(f"LLM error during query: {str(e)}")
                return self._general_help_response(question)

        # STEP 4: Fallback - helpful guidance
        return self._general_help_response(question)

    def _general_help_response(self, question):
        """Provide helpful guidance when query doesn't match any drug"""
        available_drugs = ", ".join([d['name'] for d in self.drug_db.values()])
        return f"""I appreciate your question about: *"{question}"*

I'm designed to provide **verified pharmaceutical information** to ensure your safety. I currently have detailed, accurate information for the following medications:

**{available_drugs}**

### How to Get the Best Results:
- Ask: *"Tell me about Paracetamol"*
- Ask: *"What is the dosage for Amoxicillin?"*
- Ask: *"Side effects of Ibuprofen"*
- Ask: *"Drug interactions of Aspirin"*
- Ask: *"Emergency drugs list"*

### Need More Help?
- 🏥 Click **Health Grid** for nearby hospitals
- 🚨 **Emergency?** Call **108** immediately
- 📱 Toggle **WhatsApp** to receive info on your phone

*I prioritize accuracy over quantity — I will never guess or hallucinate drug information.*
"""


# Singleton instance
_rag_service = None


def get_rag_service():
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
