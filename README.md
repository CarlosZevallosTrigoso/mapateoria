# Glosario

Visor de los mapas conceptuales del glosario. Cada ficha exportada como JSON va a la carpeta `nodos/`; al subirla, una GitHub Action fusiona todas las fichas en un solo `grafo.json`, lo valida y publica el sitio en GitHub Pages.

## Contenido del repositorio

```
index.html                    el visor
nodos/                        las fichas en JSON, una por archivo
scripts/fusionar.py           fusiona y valida las fichas
.github/workflows/grafo.yml   la Action que publica el sitio
```

`grafo.json` no se guarda en el repositorio: la Action lo genera en cada publicación.

## Puesta en marcha

1. Crea un repositorio público en GitHub (Pages en repositorios privados requiere un plan de pago).
2. Sube `index.html`, `README.md`, la carpeta `nodos/` y la carpeta `scripts/` arrastrándolas a la página del repositorio.
3. Crea la Action a mano, porque macOS oculta las carpetas que empiezan con punto y el arrastre suele omitirlas: en el repositorio, *Add file* > *Create new file*, escribe como nombre `.github/workflows/grafo.yml`, pega el contenido de ese archivo y guarda.
4. En *Settings* > *Pages*, elige *GitHub Actions* como fuente (*Source*).
5. En la pestaña *Actions* verás la primera ejecución. Cuando termine, el sitio queda en `https://TU-USUARIO.github.io/NOMBRE-DEL-REPO/`.

## Agregar fichas

Sube el nuevo JSON a `nodos/` (*Add file* > *Upload files* dentro de la carpeta). La Action se ejecuta sola y el sitio se actualiza en uno o dos minutos. El nombre del archivo es libre; lo que une las fichas entre sí son los identificadores de sus nodos, así que el mismo autor, obra o concepto debe llevar siempre el mismo identificador.

Si quieres ver cómo quedaría una ficha antes de subirla, abre el sitio, pulsa *Abrir JSON* y elige el archivo desde tu computadora. Se suma al grafo publicado solo en tu navegador, sin modificar nada en GitHub.

## Advertencias

La fusión revisa cada archivo y registra los problemas sin detener la publicación: JSON que no se puede leer, identificadores con mayúsculas o tildes, aristas que apuntan a nodos inexistentes (se descartan), ejes no declarados, nodos sin conexiones, un mismo nodo con datos distintos en dos archivos (gana el archivo con fecha de exploración más reciente) y posibles duplicados, es decir, dos identificadores distintos con la misma etiqueta. Las ves en el botón de la esquina inferior derecha del visor y en el resumen de cada ejecución en la pestaña *Actions*.

## Uso del visor

La vista *Red* agrupa las definiciones por enfoque y dibuja las relaciones entre ellas. Al tocar una definición se despliegan su autor, sus obras, sus citas y sus metáforas, y se abre la ficha completa; al tocar una relación se lee su formulación, el eje y la divergencia. *Fuentes* despliega todo a la vez. La vista *Tiempo* ordena las definiciones por año y por enfoque. En *Filtros* puedes ocultar tipos de relación, atenuar todo lo que no pertenezca a un eje y esconder los conceptos todavía no explorados. *Imagen* descarga la vista actual en PNG.

La dirección de la página cambia al seleccionar algo, así que puedes copiarla para compartir una ficha concreta.

## Si algo falla

Si el sitio muestra «No encontré datos para dibujar», revisa en *Actions* que la última ejecución haya terminado bien y que *Pages* use *GitHub Actions* como fuente. Si la ejecución falla en los pasos `configure-pages`, `upload-pages-artifact` o `deploy-pages`, es probable que GitHub haya publicado versiones nuevas de esas acciones: actualiza el número de versión en `grafo.yml`. El visor carga sus bibliotecas desde cdn.jsdelivr.net; si alguna vez prefieres no depender de esa red, se pueden copiar a una carpeta `lib/` del repositorio.
