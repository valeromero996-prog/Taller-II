# 📚 Recomendador de lecturas con reglas de asociación

**Certamen 2 · Aprendizaje no supervisado · Grupo X**
Integrantes: _______________________

🔗 **App publicada:** https://PEGAR-LINK-AQUI.streamlit.app

## Problema

Una biblioteca o librería quiere sugerir la **próxima lectura**: *"a los lectores que les gustó este libro también les gustó…"*.
Buscamos qué libros se disfrutan juntos (reglas de asociación), construimos un recomendador basado en esas reglas
y medimos si acierta más que recomendar simplemente "lo más popular".

## Datos

| | |
|---|---|
| Base | **goodbooks-10k** (Zając, 2017) |
| Fuente | https://github.com/zygmuntz/goodbooks-10k |
| Licencia | CC BY-SA 4.0 |
| Original | 5.976.479 calificaciones (1–5 ★) · 53.424 usuarios · 10.000 libros |
| **Transacción** | un lector |
| **Ítem** | un libro que el lector calificó con **4 o 5 estrellas** |
| Después de la limpieza | **9.753 lectores** (muestra de 10.000, semilla 42) · **100 libros** (los más gustados) · **14,2 libros por lector** |

## Resultados principales

- Las reglas más fuertes (lift 4–9) son dentro de una misma saga (*Twilight*, *Harry Potter*, *Game of Thrones*).
- Hay reglas entre autores útiles para descubrir lecturas: *{1984, Animal Farm} ⇒ {Brave New World}* (lift 3,5), *{Divergent} ⇒ {The Hunger Games}* (lift 1,9).
- **HitRate@10:** reglas (lift) **0,47** vs. más populares **0,22** → el recomendador acierta ≈ 2 veces más.
- Cobertura del catálogo: reglas 77 % vs. populares 41 %.

## Estructura

```
├── README.md
├── requirements.txt          ← dependencias del dashboard
├── app.py                    ← dashboard en Streamlit (5 módulos)
├── data/
│   ├── reglas.csv            ← 6.123 reglas (Fisher + Holm, redundancia)
│   ├── populares.csv         ← soporte de los 100 libros
│   ├── hitrate.csv           ← HitRate@N por estrategia
│   ├── cobertura.csv         ← % casos con regla activa y cobertura
│   └── resumen.csv           ← indicadores de la matriz
└── Certamen2_Grupo_X.ipynb   ← análisis completo (Colab)
```

## Cómo ejecutar

**Notebook:** abrir `Certamen2_Grupo_X.ipynb` en Google Colab → *Entorno de ejecución → Ejecutar todas*.
Descarga los datos directo desde GitHub (no hay que subir archivos) y tarda ≈ 3 minutos.
La última celda descarga `data.zip` con los CSV del dashboard.

**Dashboard local:**
```bash
pip install -r requirements.txt
streamlit run app.py
```

**Publicación:** https://share.streamlit.io → *Create app* → elegir este repositorio, rama `main`, archivo `app.py`.

## Uso de IA

Se usó Claude (Anthropic) como apoyo para adaptar el código de la guía de clase y estructurar el dashboard.
Todas las decisiones y resultados fueron revisados y explicados por el grupo.
