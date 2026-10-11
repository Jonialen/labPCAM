"""Build laboratory PDFs from measurements and real terminal screenshots."""

from __future__ import annotations

import csv
from html import escape
from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)


ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "evidence"
CANVAS = ROOT / "entrega_canvas"
EVIDENCE.mkdir(exist_ok=True)
CANVAS.mkdir(exist_ok=True)

FONT_DIR = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("ArialLab", str(FONT_DIR / "arial.ttf")))
pdfmetrics.registerFont(TTFont("ArialLab-Bold", str(FONT_DIR / "arialbd.ttf")))
pdfmetrics.registerFontFamily("ArialLab", normal="ArialLab", bold="ArialLab-Bold")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="LabTitle", fontName="ArialLab-Bold", fontSize=20,
                          leading=25, spaceAfter=15, textColor=colors.HexColor("#15354d")))
styles.add(ParagraphStyle(name="LabEvidenceTitle", parent=styles["LabTitle"],
                          spaceAfter=8))
styles.add(ParagraphStyle(name="LabH1", fontName="ArialLab-Bold", fontSize=12,
                          leading=16, spaceBefore=11, spaceAfter=6,
                          textColor=colors.HexColor("#17618a")))
styles.add(ParagraphStyle(name="LabEvidenceH", parent=styles["LabH1"],
                          spaceBefore=6, spaceAfter=4))
styles.add(ParagraphStyle(name="LabBody", fontName="ArialLab", fontSize=9.5,
                          leading=14, spaceAfter=7))
styles.add(ParagraphStyle(name="LabSmall", fontName="ArialLab", fontSize=8,
                          leading=11, spaceAfter=5))
styles.add(ParagraphStyle(name="LabCaption", fontName="ArialLab", fontSize=7.5,
                          leading=10, spaceAfter=6, textColor=colors.HexColor("#455967")))
styles.add(ParagraphStyle(name="LabCenter", parent=styles["LabBody"], alignment=TA_CENTER))


def P(text: str, style: str = "LabBody") -> Paragraph:
    return Paragraph(text, styles[style])


def load_results(filename: str) -> dict[str, dict[str, str]]:
    with (ROOT / filename).open(newline="", encoding="utf-8") as handle:
        return {row["config_id"]: row for row in csv.DictReader(handle)}


C = load_results("results.csv")
CPP = load_results("results_cpp.csv")
ORDER = [
    "sequential", "direct_2_static_default", "direct_4_static_default",
    "direct_8_static_default", "direct_8_static_chunk8",
    "direct_8_static_chunk32", "direct_8_static_chunk64",
    "direct_8_dynamic_chunk8", "direct_8_dynamic_chunk64",
    "direct_8_guided_default", "optimized_8_static_default",
]
LABELS = {
    "sequential": "Secuencial (1)",
    "direct_2_static_default": "Directa 2 / static",
    "direct_4_static_default": "Directa 4 / static",
    "direct_8_static_default": "Directa 8 / static",
    "direct_8_static_chunk8": "Directa 8 / static 8",
    "direct_8_static_chunk32": "Directa 8 / static 32",
    "direct_8_static_chunk64": "Directa 8 / static 64",
    "direct_8_dynamic_chunk8": "Directa 8 / dynamic 8",
    "direct_8_dynamic_chunk64": "Directa 8 / dynamic 64",
    "direct_8_guided_default": "Directa 8 / guided",
    "optimized_8_static_default": "Pares 8 / static",
}


def metric(data: dict[str, dict[str, str]], key: str, field: str) -> float:
    return float(data[key][field])


BEST_C = min(ORDER[1:-1], key=lambda key: metric(C, key, "elapsed_mean_s"))
BEST_CPP = min(ORDER[1:-1], key=lambda key: metric(CPP, key, "elapsed_mean_s"))


def result_table(results: dict[str, dict[str, str]]) -> Table:
    rows = [["Configuración", "Media (s)", "Desv. (s)", "Speedup", "Efficiency"]]
    for key in ORDER:
        row = results[key]
        rows.append([
            LABELS[key], f"{float(row['elapsed_mean_s']):.4f}",
            f"{float(row['elapsed_sd_s']):.4f}",
            f"{float(row['speedup_vs_seq']):.2f}",
            f"{float(row['efficiency']):.3f}",
        ])
    table = Table(rows, colWidths=[6.5 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#15354d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "ArialLab-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "ArialLab"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.whitesmoke, colors.HexColor("#e9f2f6")]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#15354d")),
    ]))
    return table


IMAGES = {
    key: EVIDENCE / f"{key}.png"
    for key in ("compile", "sequential", "parallel", "optimized", "hardware", "correctness")
}

cpp_output = (EVIDENCE / "logs" / "cpp_runs.txt").read_text(encoding="utf-8")
for stem, command in [
    ("cpp_sequential", "$ build/cpp_nbody_seq"),
    ("cpp_parallel", "$ build/cpp_nbody_parallel"),
    ("cpp_optimized", "$ build/cpp_nbody_optimized"),
]:
    start = cpp_output.index(command)
    following = cpp_output.find("\n$ ", start + 2)
    section = cpp_output[start:following if following != -1 else None]
    (EVIDENCE / "logs" / f"{stem}.txt").write_text(section.rstrip() + "\n",
                                                         encoding="utf-8", newline="\n")
    IMAGES[stem] = EVIDENCE / f"{stem}.png"


def chart() -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.25))
    for label, data, marker in [("C11", C, "o"), ("C++17", CPP, "s")]:
        keys = ["sequential", "direct_2_static_default", "direct_4_static_default",
                "direct_8_static_default"]
        axes[0].plot([1, 2, 4, 8], [float(data[key]["speedup_vs_seq"]) for key in keys],
                     marker=marker, label=label)
    axes[0].plot([1, 2, 4, 8], [1, 2, 4, 8], "--", color="gray", label="Ideal")
    axes[0].set(xlabel="Hilos", ylabel="Speedup", title="Escalamiento, static default")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=.25)
    keys = ["direct_8_static_default", "direct_8_dynamic_chunk8",
            "direct_8_dynamic_chunk64", "direct_8_guided_default",
            "optimized_8_static_default"]
    short = ["static", "dynamic 8", "dynamic 64", "guided", "pares static"]
    x = range(len(keys))
    axes[1].bar([i - .19 for i in x], [float(C[key]["elapsed_mean_s"]) for key in keys],
                width=.38, label="C11")
    axes[1].bar([i + .19 for i in x], [float(CPP[key]["elapsed_mean_s"]) for key in keys],
                width=.38, label="C++17")
    axes[1].set_xticks(list(x), short, rotation=25, ha="right")
    axes[1].set(ylabel="Tiempo medio (s)", title="Comparación con 8 hilos")
    axes[1].legend(fontsize=8)
    axes[1].grid(axis="y", alpha=.25)
    fig.tight_layout()
    path = EVIDENCE / "performance.png"
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path


CHART = chart()


def scaled_image(path: Path, width: float, max_height: float) -> Image:
    with PILImage.open(path) as img:
        original_width, original_height = img.size
    height = width * original_height / original_width
    if height > max_height:
        height = max_height
        width = height * original_width / original_height
    return Image(str(path), width=width, height=height)


def build_pdf(path: Path, story: list, pagesize=A4) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=pagesize,
                            rightMargin=1.8 * cm, leftMargin=1.8 * cm,
                            topMargin=1.7 * cm, bottomMargin=1.8 * cm,
                            title="Laboratorio PCAM + OpenMP: N-Body 2D",
                            author="David Domínguez, Jonathan Diaz, Luis Padilla")
    doc.build(story)


group = "David Domínguez (23712), Jonathan Diaz (23873) y Luis Padilla (23663)"
repository = "https://github.com/Jonialen/labPCAM"
group_and_repository = (
    f"<b>Integrantes:</b> {escape(group)}<br/>"
    f'<b>Repositorio:</b> <link href="{repository}" color="#17618a">{repository}</link>'
)
hardware = (EVIDENCE / "logs" / "hardware.txt").read_text(encoding="utf-8")
chip = next(line.split(":", 1)[1].strip() for line in hardware.splitlines()
            if line.startswith("Model name:"))
correctness_log = (EVIDENCE / "logs" / "correctness.txt").read_text(encoding="utf-8")
optimized_differences = [float(value) for value in re.findall(
    r"optimized_max_abs_state_difference=([0-9.eE+-]+)", correctness_log
)]
direct_differences = [float(value) for value in re.findall(
    r"direct_max_abs_state_difference=([0-9.eE+-]+)", correctness_log
)]
assert len(optimized_differences) == len(direct_differences) == 2
checksum = C["sequential"]["checksum_first"]

report: list = []
report += [P("Simulación N-Body 2D con PCAM y OpenMP", "LabTitle"),
           P(group_and_repository),
           P(f"<b>Entorno:</b> WSL2 Ubuntu 24.04; {escape(chip)}; 6 núcleos físicos, "
             "12 procesadores lógicos; GCC/G++ 13.3.0."),
           P(f"<b>Medición:</b> N=5000, 10 pasos, semilla=42, tres repeticiones "
             "por configuración."),
           P("Objetivo y modelo", "LabH1"),
           P("Se modelan cuerpos con posición, velocidad y masa. Cada paso suma la "
             "aceleración gravitatoria de los demás cuerpos con suavizado ε=0.01 y "
             "actualiza primero la velocidad y después la posición (Euler simpléctico, "
             "Δt=0.001). Las tres versiones parten de la misma secuencia SplitMix64 "
             "con semilla 42. El tiempo medido por omp_get_wtime() incluye la simulación, "
             "y excluye la inicialización y la impresión."),
           P("PCAM: Partition", "LabH1"),
           P("Se eligió partición por datos: el aporte gravitatorio de una pareja de "
             "cuerpos es la unidad fina de cálculo potencial durante un paso. La "
             "versión directa considera aportes dirigidos (i,j), j≠i; la simétrica "
             "considera cada pareja i&lt;j una vez. Las parejas pueden calcularse "
             "simultáneamente si sus resultados se acumulan con seguridad. En cambio, "
             "el paso t+1 necesita el estado completo de t; los pasos no son "
             "independientes. Separar fuerza e integración como fases funcionales "
             "no permite ejecutarlas a la vez sobre un mismo paso."),
           P("PCAM: Communication", "LabH1"),
           P("Cada contribución necesita posiciones y masas del estado actual, compartido "
             "solo para lectura; los aportes de una misma aceleración deben combinarse. "
             "La directa suma esos aportes dentro de la tarea de un cuerpo, con salida "
             "exclusiva por hilo. La simétrica aporta a dos cuerpos: guarda sumas en planos "
             "privados por hilo y, tras una barrera, reduce por cuerpo antes de integrar. "
             "Así evita carreras sin atomics. Al finalizar el paso se sincroniza el "
             "estado antes de iniciar el siguiente. Aquí comunicación significa "
             "compartir, combinar y sincronizar datos, no enviar mensajes explícitos."),
           ]

report += [P("Diseño OpenMP y costos", "LabTitle"),
           P("PCAM: Agglomeration", "LabH1"),
           P("La unidad fina identificada en P no se lanzó como una tarea OpenMP por "
             "pareja. Se agruparon N−1 aportes por cuerpo i en la directa y N−i−1 "
             "parejas por valor de i en la simétrica. Cada iteración exterior es así "
             "una tarea práctica con suficiente trabajo para amortizar la planificación. "
             "El chunk de OpenMP puede agrupar además varias iteraciones exteriores "
             "en una asignación: se midieron 8, 32, 64 y default. Cambia la "
             "granularidad de asignación, no la partición matemática inicial. "
             "Con static, el chunk explícito también cambia qué bloques recibe "
             "cada hilo; el experimento no separa A de M."),
           P("PCAM: Mapping", "LabH1"),
           P("Las tareas exteriores agrupadas se asignan a 2, 4 u 8 hilos. Static "
             "predetermina el reparto; dynamic entrega el siguiente chunk disponible; "
             "guided reduce progresivamente el tamaño de los bloques. La directa "
             "tiene casi N−1 interacciones por iteración, mientras que en la simétrica "
             "el trabajo cae de N−1 a cero, lo que puede causar espera con static. "
             "La elección equilibra trabajo ocioso y overhead de scheduling. Se "
             "midieron los tres esquemas en la versión directa con 8 hilos; "
             "en la simétrica solo se midió static para la comparación principal. "
             "Los tiempos no aíslan por sí solos la causa de sus diferencias."),
           KeepTogether([
               P("Concurrencia y memoria", "LabH1"),
               P("Si dos hilos actualizasen directamente la aceleración de i y j, habría "
                 "escrituras concurrentes. Los planos privados eliminan esa carrera y "
                 "evitan atomics por par. Su costo es O(hilos × N) memoria por paso, más "
                 "una reducción O(hilos × N). Las tres versiones conservan complejidad "
                 "asintótica O(pasos × N²); la versión por pares evalúa N(N−1)/2 parejas "
                 "en vez de N(N−1) interacciones dirigidas."),
           ]),
           P("Método de medición", "LabH1"),
           P("Cada configuración se ejecutó tres veces en el mismo equipo. Se guardó cada "
             "tiempo en results_raw.csv o results_cpp_raw.csv y se calculó media y desviación "
             "muestral en los CSV resumidos. Speedup S(p)=T₁/Tp; efficiency E(p)=S(p)/p, "
             "usando hilos reales observados. Las mediciones C y C++17 son corridas "
             "separadas; no deben compararse como un experimento apareado."),
           ]

report += [P("Resultados medidos: C11", "LabTitle"),
           P("N=5000 · 10 pasos · semilla 42 · tres repeticiones por configuración. "
             "Valores redondeados para lectura; los CSV conservan más cifras.", "LabSmall"),
           result_table(C), Spacer(1, .3 * cm),
           scaled_image(CHART, 17.0 * cm, 7.2 * cm),
           P(f"La directa con 8 hilos y static default alcanzó "
             f"{metric(C, 'direct_8_static_default', 'speedup_vs_seq'):.2f}× "
             f"(eficiencia {metric(C, 'direct_8_static_default', 'efficiency'):.3f}). "
             f"{LABELS[BEST_C]} obtuvo el menor tiempo medio de esta corrida: "
             f"{metric(C, BEST_C, 'elapsed_mean_s'):.4f} s. Los tres chunks "
             "static medidos permiten evaluar la granularidad, pero tres muestras "
             "no demuestran un orden universal. La versión por pares con static "
             f"default tardó {metric(C, 'optimized_8_static_default', 'elapsed_mean_s'):.4f} s, "
             f"{metric(C, 'optimized_8_static_default', 'elapsed_mean_s') / metric(C, 'direct_8_static_default', 'elapsed_mean_s'):.2f} "
             "veces el tiempo de la directa equivalente.", "LabSmall"),
           PageBreak()]

report += [P("Resultados medidos: C++17 y corrección", "LabTitle"),
           result_table(CPP), Spacer(1, .3 * cm),
           P(f"Con C++17, static default obtuvo "
             f"{metric(CPP, 'direct_8_static_default', 'speedup_vs_seq'):.2f}× con 8 hilos; "
             f"{LABELS[BEST_CPP]} obtuvo el menor tiempo medio "
             f"({metric(CPP, BEST_CPP, 'elapsed_mean_s'):.4f} s). "
             f"La versión por pares con static default tardó "
             f"{metric(CPP, 'optimized_8_static_default', 'elapsed_mean_s'):.4f} s "
             f"frente a {metric(CPP, 'direct_8_static_default', 'elapsed_mean_s'):.4f} s "
             "de la directa equivalente. "
             "Menos evaluaciones de pares no implicó menos tiempo total: los acumuladores, "
             "su inicialización y reducción, y el desequilibrio potencial agregan costo."),
           P("Granularidad y asignación", "LabH1"),
           P("En C11, los chunks static 8, 32 y 64 dieron 0.2082, 0.2099 y 0.2086 s: "
             "no se aprecia una ventaja clara entre esos tamaños. En C++17 dieron "
             "0.2094, 0.2166 y 0.2346 s; el chunk 64 fue el más lento de los tres "
             "en esta corrida. El chunk agrupa tareas de cuerpos (A), pero con static "
             "también cambia su reparto entre hilos (M). Con 8 hilos, la política "
             "más rápida medida fue dynamic 8 en C11 (0.1789 s) y dynamic 64 en "
             "C++17 (0.1850 s); guided dio 0.1880 y 0.1869 s, y static default "
             "0.2048 y 0.2062 s, respectivamente. Con tres repeticiones no se "
             "puede atribuir toda diferencia a la política ni afirmar que el "
             "mismo ajuste ganará en otros equipos.", "LabSmall"),
           P("Corrección numérica", "LabH1"),
           P("Para N=5000 y 10 pasos, se compararon todas las coordenadas, velocidades "
             "y masas contra la versión secuencial. Diferencia absoluta máxima: "
             f"directa={direct_differences[0]:.3g} en C y "
             f"{direct_differences[1]:.3g} en C++17; por pares="
             f"{optimized_differences[0]:.3e} en C y "
             f"{optimized_differences[1]:.3e} en C++17. "
             f"El checksum impreso fue {checksum} en las 66 mediciones, "
             "pero la comparación de estado completo es la evidencia más fuerte."),
           P("Conclusiones", "LabH1"),
           P("La paralelización directa sigue mejorando hasta 8 hilos, pero ya es "
             "sublineal con 2: en C11 los speedups static son 1.87×, 2.82× y 4.37× "
             "para 2, 4 y 8 hilos (eficiencias 0.937, 0.705 y 0.546); en C++17 son "
             "1.83×, 2.84× y 4.31× (0.914, 0.709 y 0.539). Al pasar de 4 a 8 "
             "hilos el rendimiento mejora solo 1.55× en C11 y 1.52× en C++17, "
             "frente al 2× ideal. No se esperan ocho veces más rendimiento al pasar "
             "de 8 a 64 núcleos: la eficiencia ya cae con más hilos y persisten "
             "sincronización, tráfico de memoria y costos de planificación. Esta "
             "extrapolación no se midió; el equipo utilizado tiene 6 núcleos físicos."),
           PageBreak()]

report += [P("Evidencia de compilación y ejecución", "LabTitle"),
           P("Las capturas muestran ejecuciones adicionales con la misma carga y semilla. "
             "Sus tiempos individuales pueden diferir de las medias de las tres "
             "repeticiones registradas en los CSV.", "LabSmall")]
for title, key in [("Compilación C/C++17", "compile"),
                   ("Ejecución secuencial C++17", "cpp_sequential"),
                   ("Ejecución paralela directa C++17", "cpp_parallel"),
                   ("Ejecución por pares C++17", "cpp_optimized"),
                   ("Hardware", "hardware")]:
    report.append(KeepTogether([
        P(title, "LabEvidenceH"),
        scaled_image(IMAGES[key], 15.5 * cm, 3.8 * cm),
    ]))
build_pdf(ROOT / "report.pdf", report)

pcam = [P("Explicación PCAM · N-Body 2D", "LabTitle"),
        P(group_and_repository),
        P("<b>P · Partition (dividir).</b> Se eligió partición por datos. Cada "
          "contribución gravitatoria es trabajo fino potencial: (i,j) dirigido "
          "en la directa o i&lt;j en la simétrica. Las parejas del mismo paso "
          "pueden calcularse simultáneamente si se combinan sus aportes con "
          "seguridad. El paso siguiente depende del estado completo anterior; "
          "las fases de fuerza e integración tampoco son simultáneas."),
        P("<b>C · Communication (conectar).</b> Los cuerpos actuales son lectura "
          "compartida. Los aportes de una misma aceleración se combinan: dentro "
          "de un hilo en la directa, o mediante planos privados por hilo y reducción "
          "tras una barrera en la simétrica. Un hilo integra cada cuerpo de salida. "
          "La barrera entre pasos protege la dependencia temporal; no se necesitan "
          "mensajes explícitos ni atomics por pareja."),
        P("<b>A · Agglomeration (agrupar).</b> En vez de administrar una tarea "
          "OpenMP por pareja, se agrupan N−1 aportes por cuerpo en la directa "
          "o N−i−1 parejas por i en la simétrica. El chunk agrupa después varias "
          "iteraciones exteriores en una asignación. Se midieron 8, 32 y 64 "
          "con 8 hilos; en C las medias static fueron "
          f"{metric(C, 'direct_8_static_chunk8', 'elapsed_mean_s'):.4f}, "
          f"{metric(C, 'direct_8_static_chunk32', 'elapsed_mean_s'):.4f} y "
          f"{metric(C, 'direct_8_static_chunk64', 'elapsed_mean_s'):.4f} s, "
          "respectivamente. Con static, variar chunk también modifica el reparto "
          "de bloques, por lo que este experimento mezcla A y M."),
        P("<b>M · Mapping (asignar).</b> Se distribuyen esos chunks entre hilos: "
          "static fija la distribución, dynamic entrega trabajo al liberar un "
          "hilo y guided disminuye el bloque. La directa tiene costo casi uniforme "
          "por i; la simétrica tiene costo decreciente N−i−1 y puede desbalancearse "
          "con static. "
          f"En C y 8 hilos, static default dio {metric(C, 'direct_8_static_default', 'elapsed_mean_s'):.4f} s, "
          f"dynamic 8 dio {metric(C, 'direct_8_dynamic_chunk8', 'elapsed_mean_s'):.4f} s "
          f"y guided default {metric(C, 'direct_8_guided_default', 'elapsed_mean_s'):.4f} s. "
          "El reparto dinámico puede cambiar balanceo "
          "y overhead; esta comparación de la versión directa no aísla por sí "
          "sola la causa. La simétrica solo se midió con static."),
        P("OpenMP y decisiones de implementación", "LabH1"),
        P("Se usa num_threads(requested_threads) y schedule(runtime) para comparar "
          "configuraciones sin cambiar el kernel. omp_set_schedule fija el tipo y "
          "chunk. Una barrera implícita antes de reducir los acumuladores impide "
          "leer valores incompletos. El integrador mantiene dos búferes de cuerpos "
          "para separar lectura y escritura."),
        P("Evidencia y alcance", "LabH1"),
        P("La carga fue N=5000, 10 pasos, semilla 42, tres repeticiones; los datos "
          f"crudos y resumidos están en los cuatro CSV. La directa logró "
          f"{metric(C, 'direct_8_static_default', 'speedup_vs_seq'):.2f}× "
          "con 8 hilos static frente a 1 hilo secuencial, y el estado completo "
          f"coincidió exactamente. La simétrica difirió como máximo "
          f"{optimized_differences[0]:.3e}, "
          "pero fue más lenta que la directa equivalente en esta máquina.")]
build_pdf(CANVAS / "explicacion_pcam.pdf", pcam)

evidence_story = [P("Evidencia de ejecución", "LabEvidenceTitle"),
                  P(group_and_repository),
                  P("Resultados principales", "LabH1"),
                  P(f"C11: secuencial {metric(C, 'sequential', 'elapsed_mean_s'):.4f} s; "
                    f"directa 8/static {metric(C, 'direct_8_static_default', 'elapsed_mean_s'):.4f} s "
                    f"({metric(C, 'direct_8_static_default', 'speedup_vs_seq'):.2f}×); "
                    f"por pares 8/static {metric(C, 'optimized_8_static_default', 'elapsed_mean_s'):.4f} s. "
                    f"C++17: secuencial {metric(CPP, 'sequential', 'elapsed_mean_s'):.4f} s; "
                    f"directa 8/static {metric(CPP, 'direct_8_static_default', 'elapsed_mean_s'):.4f} s "
                    f"({metric(CPP, 'direct_8_static_default', 'speedup_vs_seq'):.2f}×); "
                    f"por pares 8/static {metric(CPP, 'optimized_8_static_default', 'elapsed_mean_s'):.4f} s. "
                    "Los valores son medias de tres ejecuciones con N=5000, 10 pasos y semilla 42."),
                  P("La versión directa aceleró el cálculo respecto a la secuencial. "
                    "La versión por pares realizó menos interacciones, pero tardó más "
                    "que la directa de 8 hilos con el mismo schedule static: sus "
                    "acumuladores privados y la reducción agregan trabajo."),
                  P("Las capturas son ejecuciones adicionales con la misma carga y semilla; "
                    "sus tiempos individuales pueden diferir de las medias del CSV.",
                    "LabSmall")]
for title, key in [
    ("1. Compilación exitosa", "compile"),
    ("2. Ejecución secuencial", "sequential"),
    ("3. Ejecución paralela directa", "parallel"),
    ("4. Ejecución optimizada por pares", "optimized"),
    ("5. Hardware y compiladores", "hardware"),
    ("6. Comparación del estado completo", "correctness"),
]:
    evidence_story.append(KeepTogether([
        P(title, "LabEvidenceH"),
        scaled_image(IMAGES[key], 16 * cm, 14 * cm),
    ]))
build_pdf(CANVAS / "evidencia.pdf", evidence_story)

print("Generated report.pdf and entrega_canvas/*.pdf using evidence/*.png")
