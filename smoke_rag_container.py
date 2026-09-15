import json
import sys

sys.path.insert(0, '/app')

from app.services.ingestion import ingestion_service
from app.services.retrieval import retrieval_service

pdf_path = '/tmp/SIH26117.pdf'

def run_smoke():
    print('=== INGEST ===')
    stats = ingestion_service.ingest_pdf(
        pdf_path=pdf_path,
        doc_name='SIH26117.pdf',
        classification_tag='INTERNAL',
    )
    print(json.dumps(stats, indent=2, default=str))

    queries = [
        'Sovereign On-Premise Agentic AI Workbench',
        'confidential industrial work',
        'Smart Automation',
    ]

    for query in queries:
        print('\n=== QUERY ===')
        print(query)
        results = retrieval_service.retrieve(query=query, user_clearance=['INTERNAL'], top_k=3)
        if not results:
            print('NO RESULTS')
            continue

        for i, result in enumerate(results, start=1):
            print(f'-- result {i} --')
            print('doc:', result.doc_name)
            print('page:', result.page)
            print('section:', result.section_title)
            print('tag:', result.classification_tag)
            print('rerank_score:', result.rerank_score)
            print(result.text[:1200])
            print()

if __name__ == '__main__':
    run_smoke()
