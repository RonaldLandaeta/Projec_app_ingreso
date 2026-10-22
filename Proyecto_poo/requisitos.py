import json
from dataclasses import dataclass, field

ARCHIVO = "datos.json"

# ---------- perfiles ----------
PERFILES = ["Alumno", "Beca trabajo", "Deportista", "Ayudante especial"]
PROFESOR = "Profesor"

# ---------- tipos de error ----------
TIPO_INSCRIBIR = "No pude inscribir"
TIPO_HORARIO = "Cambio de horario"
TIPOS_ERROR = [TIPO_INSCRIBIR, TIPO_HORARIO]

MOTIVO_PRERREQ = "Prerrequisito"     # debes ver una materia ANTES
MOTIVO_COREQ = "Correquisito"        # debes ver 2 materias AL MISMO TIEMPO

# (nrc, nombre, horario, profesor, prerrequisitos, correquisitos)
MATERIAS_EJEMPLO = [
    # --- 7 materias originales (con requisitos) ---
    (10234, "Cálculo I",         "Lunes y Miércoles 07:00-09:00",   "Ana Torres",     [20101], []),
    (10567, "Programación I",    "Martes y Jueves 09:00-11:00",     "Carlos Mendoza", [20102], [20106]),
    (11890, "Física I",          "Lunes y Viernes 11:00-13:00",     "Luis Paredes",   [],      [20103]),
    (12045, "Álgebra Lineal",    "Miércoles y Viernes 07:00-09:00", "María Salazar",  [20101], []),
    (13321, "Base de Datos",     "Martes y Jueves 14:00-16:00",     "Jorge Ríos",     [20105], []),
    (14478, "Inglés Técnico",    "Sábado 08:00-12:00",              "Laura Vega",     [20107], []),
    (15002, "Estadística",       "Lunes y Miércoles 15:00-17:00",   "Pedro Castillo", [10234], []),
    # --- 7 materias creadas para los requisitos ---
    (20101, "Matemática Básica",               "Lunes y Miércoles 09:00-11:00",   "Rosa Quintero",  [],      []),
    (20102, "Introducción a la Programación",  "Martes y Jueves 07:00-09:00",     "Daniel Soto",    [],      []),
    (20103, "Laboratorio de Física I",         "Viernes 14:00-16:00",             "Elena Barrios",  [],      [11890]),
    (20104, "Cálculo II",                      "Martes y Jueves 11:00-13:00",     "Héctor Lara",    [10234], []),
    (20105, "Estructuras de Datos",            "Miércoles y Viernes 09:00-11:00", "Sofía Navarro",  [10567], []),
    (20106, "Laboratorio de Programación I",   "Miércoles 17:00-19:00",           "Andrés Molina",  [],      [10567]),
    (20107, "Inglés Básico",                   "Sábado 13:00-17:00",              "Camila Ortiz",   [],      []),
]


@dataclass
class Materia:
    nombre: str
    nrc: int                                    # máximo 5 dígitos
    horario: str                                # contiene día/s y hora/s
    profesor: str
    prerrequisitos: list = field(default_factory=list)   # NRC que debes ver ANTES
    correquisitos: list = field(default_factory=list)    # NRC que debes ver AL MISMO TIEMPO


@dataclass
class Problema:
    tipo_error: str
    motivo: str = ""                            # solo para "No pude inscribir"
    cantidad_problemas: int = 0                 # veces que fue reportado
    nrcs_afectados: set = field(default_factory=set)
    reportes_por_perfil: dict = field(default_factory=dict)

    @property
    def nombre(self):
        return f"{self.tipo_error} ({self.motivo})" if self.motivo else self.tipo_error

    def registrar_ocurrencia(self, nrc: int, relacionadas, perfil: str):
        self.cantidad_problemas += 1
        self.nrcs_afectados.add(nrc)
        self.nrcs_afectados.update(relacionadas)
        self.reportes_por_perfil[perfil] = self.reportes_por_perfil.get(perfil, 0) + 1

    def prioridad(self):
        # Prioriza por cantidad de materias afectadas y luego por reportes
        return (len(self.nrcs_afectados), self.cantidad_problemas)


@dataclass
class Estudiante:
    ci: str
    nombre: str
    correo: str
    perfil: str = "Alumno"      # Alumno, Beca trabajo, Deportista, Ayudante especial

    def reportar_problema(self, sistema, tipo_error: str, nrc: int, motivo: str = "") -> bool:
        materia = sistema.materias.get(nrc)
        if materia is None:
            print("  ! Esa materia (NRC) no existe.")
            return False

        relacionadas = []
        if tipo_error == TIPO_INSCRIBIR:
            if motivo == MOTIVO_PRERREQ:
                relacionadas = materia.prerrequisitos
            elif motivo == MOTIVO_COREQ:
                relacionadas = materia.correquisitos
            if not relacionadas:
                print(f"  ! {materia.nombre} no tiene {motivo.lower()}s registrados.")
                return False

        nuevo = Problema(tipo_error, motivo)
        problema = sistema.problemas.setdefault(nuevo.nombre, nuevo)
        problema.registrar_ocurrencia(nrc, relacionadas, self.perfil)
        print(f"  ✔ '{problema.nombre}' reportado por {self.nombre} ({self.perfil}) en {materia.nombre}.")
        if relacionadas:
            print(f"    Materias involucradas: {sistema.nombres(relacionadas)}")
        return True


def pedir_nrc(mensaje):
    """Pide un NRC numérico de máximo 5 dígitos."""
    while True:
        valor = input(mensaje).strip()
        if valor.isdigit() and 1 <= len(valor) <= 5:
            return int(valor)
        print("  ! El NRC debe ser numérico y de máximo 5 dígitos.")


class Sistema:
    def __init__(self):
        self.materias = {}      # nrc -> Materia
        self.estudiantes = {}   # ci -> Estudiante
        self.problemas = {}     # nombre del problema -> Problema
        self.cargar_materias_ejemplo()

    def cargar_materias_ejemplo(self):
        for nrc, nombre, horario, profesor, pre, co in MATERIAS_EJEMPLO:
            self.materias[nrc] = Materia(nombre, nrc, horario, profesor, list(pre), list(co))

    def nombres(self, nrcs):
        return ", ".join(f"[{n}] {self.materias[n].nombre}" for n in nrcs)

    def pedir_lista_nrc(self, mensaje):
        """Lee NRC separados por coma; deben existir. Enter = ninguno."""
        while True:
            texto = input(mensaje).strip()
            if not texto:
                return []
            partes = [p.strip() for p in texto.split(",")]
            if all(p.isdigit() and len(p) <= 5 and int(p) in self.materias for p in partes):
                return [int(p) for p in partes]
            print("  ! Todos los NRC deben ser numéricos (máx. 5 dígitos) y existir en el sistema.")

    # ---------- inicio: elegir perfil ----------
    def elegir_perfil(self):
        """Devuelve un perfil de estudiante, PROFESOR, o None para salir."""
        while True:
            op = input("""
=== ¿CUÁL ES TU PERFIL? ===
1. Alumno
2. Beca trabajo
3. Deportista
4. Ayudante especial
5. Profesor
6. Salir
> """).strip()
            if op in ("1", "2", "3", "4"):
                return PERFILES[int(op) - 1]
            if op == "5":
                return PROFESOR
            if op == "6":
                return None
            print("  ! Opción inválida.")

    # ---------- paso 1: registro ----------
    def registrar_o_ingresar(self, perfil: str) -> Estudiante:
        print(f"\n--- PASO 1: REGISTRO ({perfil}) ---")
        ci = input("CI: ").strip()
        if ci in self.estudiantes:
            est = self.estudiantes[ci]
            if est.perfil != perfil:
                est.perfil = perfil
                print(f"  Perfil actualizado a: {perfil}")
            print(f"  Bienvenido de nuevo, {est.nombre} ({est.perfil}).")
            return est
        nombre = input("Nombre: ").strip()
        correo = input("Correo: ").strip()
        est = Estudiante(ci, nombre, correo, perfil)
        self.estudiantes[ci] = est
        print(f"  ✔ {nombre} registrado como {perfil}.")
        return est

    # ---------- paso 2: reportar problema ----------
    def pedir_motivo(self) -> str:
        print("¿Por qué no pudiste inscribir?")
        print("  1. Prerrequisito (me falta ver una materia antes)")
        print("  2. Correquisito (debo inscribir otra materia al mismo tiempo)")
        while True:
            op = input("> ").strip()
            if op == "1":
                return MOTIVO_PRERREQ
            if op == "2":
                return MOTIVO_COREQ
            print("  ! Elige 1 o 2.")

    def reportar(self, est: Estudiante):
        print("\n--- REPORTAR PROBLEMA ---")
        self.mostrar_materias()
        nrc = pedir_nrc("NRC de la materia afectada: ")
        if nrc not in self.materias:
            print("  ! Ese NRC no existe.")
            return
        print("Tipo de error:")
        for i, t in enumerate(TIPOS_ERROR, 1):
            print(f"  {i}. {t}")
        print(f"  {len(TIPOS_ERROR) + 1}. Otro")
        op = input("> ").strip()
        motivo = ""
        if op.isdigit() and 1 <= int(op) <= len(TIPOS_ERROR):
            tipo = TIPOS_ERROR[int(op) - 1]
            if tipo == TIPO_INSCRIBIR:
                motivo = self.pedir_motivo()
        else:
            tipo = input("Describe el tipo de error: ").strip() or "Otro"
        if est.reportar_problema(self, tipo, nrc, motivo):
            self.guardar(silencioso=True)       # queda guardado para el reporte del profesor

    # ---------- consultas ----------
    def mostrar_materias(self):
        print(f"  {'NRC':<5} | {'Materia':<30} | {'Horario':<32} | Profesor")
        print("  " + "-" * 94)
        for m in self.materias.values():
            print(f"  {m.nrc:<5} | {m.nombre:<30} | {m.horario:<32} | {m.profesor}")

    def mostrar_requisitos(self):
        hay = False
        for m in self.materias.values():
            if not (m.prerrequisitos or m.correquisitos):
                continue
            hay = True
            pre = self.nombres(m.prerrequisitos) if m.prerrequisitos else "-"
            co = self.nombres(m.correquisitos) if m.correquisitos else "-"
            print(f"  [{m.nrc}] {m.nombre}")
            print(f"      Prerrequisito: {pre}")
            print(f"      Correquisito : {co}")
        if not hay:
            print("  No hay requisitos registrados.")

    def registrar_materia_nueva(self):
        nombre = input("Nombre de la materia: ").strip()
        nrc = pedir_nrc("Código de materia (NRC, máx. 5 dígitos): ")
        horario = input("Indique días y horas: ").strip()
        profesor = input("Indique nombre del profesor: ").strip()
        pre = self.pedir_lista_nrc("Prerrequisitos (NRC separados por coma, Enter si ninguno): ")
        co = self.pedir_lista_nrc("Correquisitos (NRC separados por coma, Enter si ninguno): ")
        self.materias[nrc] = Materia(nombre, nrc, horario, profesor, pre, co)
        print("  ✔ Materia registrada.")

    # ---------- reporte general (solo profesor) ----------
    def reporte_general(self):
        total = sum(p.cantidad_problemas for p in self.problemas.values())
        print("\n=== REPORTE GENERAL DE PROBLEMAS ===")
        print(f"  Estudiantes registrados : {len(self.estudiantes)}")
        print(f"  Total de reportes       : {total}")
        print(f"  Tipos de problema       : {len(self.problemas)}")
        if not self.problemas:
            print("\n  No hay problemas reportados.")
            return
        print("\n  Problemas priorizados (por materias afectadas y reportes):")
        ordenados = sorted(self.problemas.values(), key=lambda p: p.prioridad(), reverse=True)
        for i, p in enumerate(ordenados, 1):
            nombres = [self.materias[n].nombre for n in sorted(p.nrcs_afectados) if n in self.materias]
            perfiles = ", ".join(f"{k} {v}" for k, v in p.reportes_por_perfil.items()) or "-"
            print(f"  {i}. {p.nombre} -> {len(p.nrcs_afectados)} materia(s), {p.cantidad_problemas} reporte(s)")
            print(f"     Materias  : {', '.join(nombres)}")
            print(f"     Por perfil: {perfiles}")

    # ---------- sesiones ----------
    def sesion_estudiante(self, perfil: str) -> bool:
        """Devuelve True si el usuario quiere salir del programa."""
        est = self.registrar_o_ingresar(perfil)          # Paso 1: registrarse
        print("\n--- PASO 2: REGISTRA UN PROBLEMA ---")
        self.reportar(est)                               # Paso 2: registrar un problema
        menu = """
=== MENÚ ===
1. Reportar otro problema
2. Ver materias
3. Ver requisitos (pre y correquisitos)
4. Registrar materia nueva
5. Cambiar de usuario
6. Guardar y salir
> """
        while True:
            op = input(menu).strip()
            if op == "1": self.reportar(est)
            elif op == "2": self.mostrar_materias()
            elif op == "3": self.mostrar_requisitos()
            elif op == "4": self.registrar_materia_nueva()
            elif op == "5": return False
            elif op == "6": return True
            else: print("  Opción inválida.")

    def sesion_profesor(self) -> bool:
        """El profesor solo puede ver el reporte general."""
        nombre = input("Nombre del profesor: ").strip()
        print(f"\n  Bienvenido/a, profesor/a {nombre}.")
        self.reporte_general()
        menu = """
=== MENÚ PROFESOR ===
1. Ver reporte general
2. Cambiar de usuario
3. Salir
> """
        while True:
            op = input(menu).strip()
            if op == "1": self.reporte_general()
            elif op == "2": return False
            elif op == "3": return True
            else: print("  Opción inválida.")

    # ---------- persistencia ----------
    def guardar(self, silencioso=False):
        datos = {
            "materias": [vars(m) for m in self.materias.values()],
            "estudiantes": [vars(e) for e in self.estudiantes.values()],
            "problemas": [
                {"tipo_error": p.tipo_error,
                 "motivo": p.motivo,
                 "cantidad_problemas": p.cantidad_problemas,
                 "nrcs_afectados": sorted(p.nrcs_afectados),
                 "reportes_por_perfil": p.reportes_por_perfil}
                for p in self.problemas.values()
            ],
        }
        with open(ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        if not silencioso:
            print(f"  Datos guardados en {ARCHIVO}")

    def cargar(self):
        try:
            with open(ARCHIVO, encoding="utf-8") as f:
                datos = json.load(f)
        except FileNotFoundError:
            return
        for m in datos.get("materias", []):
            if m["nrc"] not in self.materias:      # las de ejemplo siempre se mantienen
                self.materias[m["nrc"]] = Materia(**m)
        for e in datos.get("estudiantes", []):
            self.estudiantes[e["ci"]] = Estudiante(**e)
        for p in datos.get("problemas", []):
            problema = Problema(
                p["tipo_error"], p.get("motivo", ""), p["cantidad_problemas"],
                set(p["nrcs_afectados"]), dict(p.get("reportes_por_perfil", {})))
            self.problemas[problema.nombre] = problema
        print(f"  Datos cargados desde {ARCHIVO}")


def main():
    s = Sistema()
    s.cargar()
    print("=== SIMULADOR DE HORARIOS ===")
    while True:
        perfil = s.elegir_perfil()
        if perfil is None:
            s.guardar()
            break
        salir = s.sesion_profesor() if perfil == PROFESOR else s.sesion_estudiante(perfil)
        if salir:
            s.guardar()
            break


if __name__ == "__main__":
    main()
