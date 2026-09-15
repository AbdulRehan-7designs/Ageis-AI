import fitz

doc = fitz.open('d:/SIH/Ageis AI/SIH26117.pdf')
print('pages', len(doc))
for i in range(min(3, len(doc))):
    txt = doc[i].get_text('text')
    print('---PAGE', i + 1, '---')
    print(txt[:1500])
