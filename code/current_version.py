import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import MapBox
from datetime import datetime

import matplotlib.pyplot as plt
import seaborn as sns

# Zum Anzeigen von PNG-Dateien in Tkinter
from PIL import Image, ImageTk

# Für die interaktive Karte
# Bitte vorab installieren: pip install tkintermapview
from tkintermapview import TkinterMapView

DATA_FILE = "traffic_diary.csv"
USER_FILE = "users.csv"
MAPBOX_API_KEY = "pk.eyJ1IjoibWF0dGhpYXNoZmwiLCJhIjoiY201ZWI5dzBkMjU2MjJ1czc2ZTI0OTlnNyJ9.6DFtWqtEQp5ufQeodVZ5dQ"
CHART_DIRECTORY = "charts"

geolocator = MapBox(api_key=MAPBOX_API_KEY)

def handle_error(msg, label):
    """Zeigt eine Fehlermeldung im GUI an."""
    label.config(text=msg, foreground="red")

def show_success(msg, label):
    """Zeigt eine Erfolgsnachricht im GUI an."""
    label.config(text=msg, foreground="green")

def create_chart_directory():
    """Erzeugt den Ordner für Diagramme, wenn er nicht existiert."""
    if not os.path.exists(CHART_DIRECTORY):
        os.makedirs(CHART_DIRECTORY)

def parse_or_reverse_geocode(s):
    """
    Prüft, ob 's' Koordinaten oder Textadresse ist.
    Ist es Koordinate (lat, lon) -> Reverse-Geocoding
    Sonst -> Forward-Geocoding
    """
    # Falls Komma vorhanden, versuchen wir "lat, lon" zu parsen
    if "," in s:
        try:
            lat_str, lon_str = s.split(",")
            lat = float(lat_str.strip())
            lon = float(lon_str.strip())
            # Reverse-Geocoding: aus Koordinaten Adresse bekommen
            # (Für reine Distanzberechnung reicht es, Koordinaten zurückzugeben.)
            location = geolocator.reverse((lat, lon))
            # location kann None sein, falls kein Eintrag gefunden
            if location:
                return (lat, lon)
            else:
                return None
        except ValueError:
            # Parsing fehlgeschlagen -> normal geocoden
            pass

    # Standard: Forward-Geocoding (Adresssuche)
    loc = geolocator.geocode(s)
    if loc:
        return (loc.latitude, loc.longitude)
    else:
        return None

def calculate_distance(start_point, end_point):
    """
    Berechnet die Distanz (in km) zwischen zwei Adressen/Koordinaten
    (start_point, end_point) mithilfe von geopy.
    """
    try:
        start_coords = parse_or_reverse_geocode(start_point)
        end_coords = parse_or_reverse_geocode(end_point)

        if not start_coords or not end_coords:
            return None

        return geodesic(start_coords, end_coords).kilometers

    except:
        return None

def save_to_csv(data, file_name):
    """
    Speichert einen Dictionary-Eintrag als neue Zeile in einer CSV-Datei.
    Existiert die Datei nicht, wird sie neu erstellt; sonst wird die Zeile angehängt.
    """
    df = pd.DataFrame([data])
    if not os.path.exists(file_name):
        df.to_csv(file_name, index=False)
    else:
        df.to_csv(file_name, mode="a", header=False, index=False)

def load_csv(file_name):
    """
    Lädt eine CSV-Datei als pandas DataFrame und gibt sie zurück.
    Existiert die Datei nicht, wird None zurückgegeben.
    """
    if not os.path.exists(file_name):
        return None
    return pd.read_csv(file_name)

class TrafficDiaryApp:
    """
    Haupt-Klasse für die Tkinter-Anwendung.
    Enthält alle GUI-Elemente und die zugehörige Logik.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Traffic Diary Analysis Tool")

        # -----------------------------------
        # Zeile 0: Benutzer-Auswahl
        # -----------------------------------
        ttk.Label(root, text="Benutzer/in:").grid(row=0, column=0, padx=5, pady=5)
        self.user_var = tk.StringVar()
        self.user_menu = ttk.Combobox(root, textvariable=self.user_var, state="readonly")
        self.user_menu.grid(row=0, column=1, padx=5, pady=5)

        # Benutzer in die Combobox laden
        self.load_users()

        # Button zum Hinzufügen neuer Benutzer
        ttk.Button(root, text="Neue/n Benutzer/in anlegen", command=self.add_new_user).grid(
            row=0, column=2, padx=5, pady=5
        )

        # -----------------------------------
        # Zeile 1: Startdatum
        # -----------------------------------
        ttk.Label(root, text="Startdatum:").grid(row=1, column=0, padx=5, pady=5)
        self.start_date_var = tk.StringVar()
        self.start_date_btn = ttk.Button(root, text="Startdatum wählen", command=self.select_start_date)
        self.start_date_btn.grid(row=1, column=1, padx=5, pady=5)
        self.start_date_label = ttk.Label(root, textvariable=self.start_date_var)
        self.start_date_label.grid(row=1, column=2, padx=5, pady=5)

        # -----------------------------------
        # Zeile 2: Enddatum
        # -----------------------------------
        ttk.Label(root, text="Enddatum:").grid(row=2, column=0, padx=5, pady=5)
        self.end_date_var = tk.StringVar()
        self.end_date_btn = ttk.Button(root, text="Enddatum wählen", command=self.select_end_date)
        self.end_date_btn.grid(row=2, column=1, padx=5, pady=5)
        self.end_date_label = ttk.Label(root, textvariable=self.end_date_var)
        self.end_date_label.grid(row=2, column=2, padx=5, pady=5)

        # -----------------------------------
        # Zeile 3: Startzeit
        # -----------------------------------
        ttk.Label(root, text="Startzeit:").grid(row=3, column=0, padx=5, pady=5)
        self.start_time_var = tk.StringVar()
        self.start_time_btn = ttk.Button(root, text="Startzeit wählen", command=self.select_start_time)
        self.start_time_btn.grid(row=3, column=1, padx=5, pady=5)
        self.start_time_label = ttk.Label(root, textvariable=self.start_time_var)
        self.start_time_label.grid(row=3, column=2, padx=5, pady=5)

        # -----------------------------------
        # Zeile 4: Endzeit
        # -----------------------------------
        ttk.Label(root, text="Endzeit:").grid(row=4, column=0, padx=5, pady=5)
        self.end_time_var = tk.StringVar()
        self.end_time_btn = ttk.Button(root, text="Endzeit wählen", command=self.select_end_time)
        self.end_time_btn.grid(row=4, column=1, padx=5, pady=5)
        self.end_time_label = ttk.Label(root, textvariable=self.end_time_var)
        self.end_time_label.grid(row=4, column=2, padx=5, pady=5)

        # -----------------------------------
        # Zeile 5: Startpunkt
        # -----------------------------------
        ttk.Label(root, text="Startpunkt:").grid(row=5, column=0, padx=5, pady=5)
        self.start_point_var = tk.StringVar()
        self.start_point_entry = ttk.Entry(root, textvariable=self.start_point_var)
        self.start_point_entry.grid(row=5, column=1, padx=5, pady=5)
        # Klick ins Feld -> Karte für Startpunkt
        self.start_point_entry.bind("<Button-1>", self.open_map_for_startpoint)

        # -----------------------------------
        # Zeile 6: Endpunkt
        # -----------------------------------
        ttk.Label(root, text="Endpunkt:").grid(row=6, column=0, padx=5, pady=5)
        self.end_point_var = tk.StringVar()
        self.end_point_entry = ttk.Entry(root, textvariable=self.end_point_var)
        self.end_point_entry.grid(row=6, column=1, padx=5, pady=5)
        # Klick ins Feld -> Karte für Endpunkt
        self.end_point_entry.bind("<Button-1>", self.open_map_for_endpoint)

        # -----------------------------------
        # Zeile 7: Verkehrsmittel (+ Fragezeichen #1)
        # -----------------------------------
        ttk.Label(root, text="Verkehrsmittel:").grid(row=7, column=0, padx=5, pady=5)
        self.mode_var = tk.StringVar(value="")
        mode_list = ["Fahrrad", "Fuß", "MIV", "MIV-Mitfahrer", "Sonstiges", "ÖV"]
        mode_list_sorted = sorted(mode_list, key=str.lower)
        self.mode_box = ttk.Combobox(
            root,
            textvariable=self.mode_var,
            values=mode_list_sorted,
            state="readonly"
        )
        self.mode_box.grid(row=7, column=1, padx=5, pady=5)

        # Tooltip-Fenster für Verkehrsmittel
        self.tooltip_window_mode = None
        self.question_mark_label_mode = ttk.Label(root, text="❓", foreground="blue", cursor="hand2")
        self.question_mark_label_mode.grid(row=7, column=2, padx=5, pady=5)

        # Events für den Verkehrsmittel-Tooltip
        self.question_mark_label_mode.bind("<Enter>", self.show_mode_tooltip)
        self.question_mark_label_mode.bind("<Leave>", self.hide_mode_tooltip)

        # -----------------------------------
        # Zeile 8: Wegezweck (+ Fragezeichen #2)
        # -----------------------------------
        ttk.Label(root, text="Wegezweck:").grid(row=8, column=0, padx=5, pady=5)
        self.purpose_var = tk.StringVar(value="")
        purpose_list = ["Arbeit", "Dienstlich", "Ausbildung", "Einkauf", "Erledigung", "Freizeit", "Begleitung"]
        purpose_list_sorted = sorted(purpose_list, key=str.lower)
        self.purpose_box = ttk.Combobox(
            root,
            textvariable=self.purpose_var,
            values=purpose_list_sorted,
            state="readonly"
        )
        self.purpose_box.grid(row=8, column=1, padx=5, pady=5)

        # Tooltip-Fenster für Wegezweck
        self.tooltip_window_purpose = None
        self.question_mark_label_purpose = ttk.Label(root, text="❓", foreground="blue", cursor="hand2")
        self.question_mark_label_purpose.grid(row=8, column=2, padx=5, pady=5)

        # Events für den Wegezweck-Tooltip
        self.question_mark_label_purpose.bind("<Enter>", self.show_purpose_tooltip)
        self.question_mark_label_purpose.bind("<Leave>", self.hide_purpose_tooltip)

        # -----------------------------------
        # Zeile 9: Speichern-Button
        # -----------------------------------
        ttk.Button(root, text="Speichern", command=self.save_entry).grid(
            row=9, column=0, columnspan=2, padx=5, pady=10
        )

        # -----------------------------------
        # Zeile 10: Auswerten-Button
        # -----------------------------------
        ttk.Button(root, text="Jetzt auswerten", command=self.analyze_data).grid(
            row=10, column=0, columnspan=2, padx=5, pady=10
        )

        # -----------------------------------
        # Zeile 11: Zurücksetzen-Button
        # -----------------------------------
        ttk.Button(root, text="Zurücksetzen", command=self.reset_all).grid(
            row=11, column=0, columnspan=2, padx=5, pady=10
        )

        # -----------------------------------
        # Zeile 12: Meldungs-Label
        # -----------------------------------
        self.message_label = ttk.Label(root, text="")
        self.message_label.grid(row=12, column=0, columnspan=3, padx=5, pady=5)

        # Meldung zurücksetzen bei Änderungen
        self.start_point_var.trace_add("write", self.clear_message)
        self.end_point_var.trace_add("write", self.clear_message)
        self.mode_var.trace_add("write", self.clear_message)
        self.user_var.trace_add("write", self.clear_message)
        self.start_time_var.trace_add("write", self.clear_message)
        self.end_time_var.trace_add("write", self.clear_message)
        self.purpose_var.trace_add("write", self.clear_message)
        self.start_date_var.trace_add("write", self.clear_message)
        self.end_date_var.trace_add("write", self.clear_message)

    # --------------------------------------------------
    #  Tooltip-Methoden für Verkehrsmittel
    # --------------------------------------------------
    def show_mode_tooltip(self, event):
        """Tooltip für das Verkehrsmittel (erste Fragezeichen)."""
        if self.tooltip_window_mode is not None:
            return  # Schon offen

        # Toplevel-Fenster ohne Rahmen
        self.tooltip_window_mode = tk.Toplevel(self.root)
        self.tooltip_window_mode.wm_overrideredirect(True)

        # Position (x, y) leicht unterhalb des Fragezeichens
        x = event.x_root
        y = event.y_root + 20
        self.tooltip_window_mode.geometry(f"+{x}+{y}")

        # Rahmen um den Tooltip
        table_frame = tk.Frame(self.tooltip_window_mode, background="white", relief="solid", borderwidth=1)
        table_frame.pack()

        # Kopfzeile fett
        header_text = f"{'Verkehrsmittel':<15}{'Hierzu gehören':<40}"
        header_label = tk.Label(
            table_frame,
            text=header_text,
            font=("Consolas", 10, "bold"),  # fett, Monospace
            background="white",
            justify="left"
        )
        header_label.pack(anchor="w", padx=5, pady=(5, 2))

        # Körper normal
        body_text = (
            f"{'Fahrrad':<15}Pedelec, Lastenrad, E-Scooter, Cityroller etc.\n"
            f"{'Fuß':<15}\n"
            f"{'MIV':<15}\n"
            f"{'MIV-Mitfahrer':<15}Mitfahrten, Taxifahrten etc.\n"
            f"{'Sonstiges':<15}Schiff, Flugzeug, Rakete etc.\n"
            f"{'ÖV':<15}\n"
        )
        body_label = tk.Label(
            table_frame,
            text=body_text,
            font=("Consolas", 10),
            background="white",
            justify="left"
        )
        body_label.pack(anchor="w", padx=5, pady=(0, 5))

    def hide_mode_tooltip(self, event):
        """Tooltip-Fenster schließen, wenn der Mauszeiger das Fragezeichen (Verkehrsmittel) verlässt."""
        if self.tooltip_window_mode is not None:
            self.tooltip_window_mode.destroy()
            self.tooltip_window_mode = None

    # --------------------------------------------------
    #  Tooltip-Methoden für Wegezweck (zweites Fragezeichen)
    # --------------------------------------------------
    def show_purpose_tooltip(self, event):
        """Tooltip für den Wegezweck (zweites Fragezeichen)."""
        if self.tooltip_window_purpose is not None:
            return  # Schon offen

        # Toplevel-Fenster ohne Rahmen
        self.tooltip_window_purpose = tk.Toplevel(self.root)
        self.tooltip_window_purpose.wm_overrideredirect(True)

        # Position (x, y) leicht unterhalb des Fragezeichens
        x = event.x_root
        y = event.y_root + 20
        self.tooltip_window_purpose.geometry(f"+{x}+{y}")

        # Rahmen um den Tooltip
        table_frame = tk.Frame(self.tooltip_window_purpose, background="white", relief="solid", borderwidth=1)
        table_frame.pack()

        # Kopfzeile fett
        header_text = f"{'Wegezweck':<12}{'Beispiel'}"
        header_label = tk.Label(
            table_frame,
            text=header_text,
            font=("Consolas", 10, "bold"),  # fett
            background="white",
            justify="left"
        )
        header_label.pack(anchor="w", padx=5, pady=(5, 2))

        # Körper normal
        body_text = (
            f"{'Arbeit':<12}Weg zur Arbeitsstätte\n"
            f"{'Ausbildung':<12}Zur Universität, zur Schule etc.\n"
            f"{'Begleitung':<12}Kind zur Schule bringen\n"
            f"{'Dienstlich':<12}Dienstreise, Weg während der Arbeit\n"
            f"{'Einkauf':<12}Lebensmittel/Getränke im Supermarkt\n"
            f"{'Erledigung':<12}Arztbesuch\n"
            f"{'Freizeit':<12}Weg nach Hause, zur Mensa, zum Sport,\n"
            "            zu Freunden etc.\n\n"
            "Wege zurück nach Hause sind immer Freizeit-Wege!"
        )
        body_label = tk.Label(
            table_frame,
            text=body_text,
            font=("Consolas", 10),
            background="white",
            justify="left"
        )
        body_label.pack(anchor="w", padx=5, pady=(0, 5))

    def hide_purpose_tooltip(self, event):
        """Tooltip-Fenster schließen, wenn der Mauszeiger das Fragezeichen (Wegezweck) verlässt."""
        if self.tooltip_window_purpose is not None:
            self.tooltip_window_purpose.destroy()
            self.tooltip_window_purpose = None

    # --------------------------------------------------
    # Lese- und Schreibfunktionen für Benutzer
    # --------------------------------------------------
    def load_users(self):
        """Lädt die Benutzer aus der CSV-Datei und befüllt das Dropdown-Menü."""
        self.user_menu['values'] = []
        if os.path.exists(USER_FILE):
            users = pd.read_csv(USER_FILE)
            user_list = sorted(users["Vorname"] + " " + users["Nachname"])
            self.user_menu['values'] = user_list

    def add_new_user(self):
        """Öffnet ein neues Fenster, um einen neuen Benutzer anzulegen."""
        def save_user(event=None):
            first_name = first_name_var.get().strip()
            last_name = last_name_var.get().strip()
            if not first_name or not last_name:
                handle_error("Bitte Vor- und Nachname angeben.", message_label)
                return

            user_full_name = f"{first_name} {last_name}"
            user_full_name_lower = user_full_name.lower()

            if os.path.exists(USER_FILE):
                existing_users = pd.read_csv(USER_FILE)
                existing_full_names_lower = (
                    existing_users["Vorname"].str.lower() + " " + existing_users["Nachname"].str.lower()
                )
                if user_full_name_lower in existing_full_names_lower.values:
                    handle_error("Benutzer/in bereits vorhanden.", message_label)
                    return

            new_user = pd.DataFrame([{"Vorname": first_name, "Nachname": last_name}])
            if not os.path.exists(USER_FILE):
                new_user.to_csv(USER_FILE, index=False)
            else:
                existing_users = pd.read_csv(USER_FILE)
                updated_users = pd.concat([existing_users, new_user], ignore_index=True)
                updated_users.to_csv(USER_FILE, index=False)

            self.load_users()
            self.user_var.set(user_full_name)
            user_window.destroy()

        user_window = tk.Toplevel(self.root)
        user_window.title("Neue/n Benutzer/in anlegen")

        ttk.Label(user_window, text="Vorname:").grid(row=0, column=0, padx=5, pady=5)
        first_name_var = tk.StringVar()
        first_name_entry = ttk.Entry(user_window, textvariable=first_name_var)
        first_name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(user_window, text="Nachname:").grid(row=1, column=0, padx=5, pady=5)
        last_name_var = tk.StringVar()
        last_name_entry = ttk.Entry(user_window, textvariable=last_name_var)
        last_name_entry.grid(row=1, column=1, padx=5, pady=5)

        message_label = ttk.Label(user_window, text="")
        message_label.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        save_button = ttk.Button(user_window, text="Speichern", command=save_user)
        save_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        first_name_entry.focus()
        user_window.bind("<Return>", save_user)

    # --------------------------------------------------
    # NEUE METHODEN: Datum wählen (Kalender)
    # --------------------------------------------------
    def select_start_date(self):
        self.select_date(self.start_date_var, "Startdatum")

    def select_end_date(self):
        self.select_date(self.end_date_var, "Enddatum")

    def select_date(self, variable, title):
        top = tk.Toplevel(self.root)
        top.title(title)

        cal = Calendar(top, selectmode="day", date_pattern="dd.mm.yyyy")
        cal.pack(pady=10)

        def on_date_selected(event):
            date = cal.get_date()
            variable.set(date)
            top.destroy()

        cal.bind("<<CalendarSelected>>", on_date_selected)

    # --------------------------------------------------
    # NEUE METHODEN: Uhrzeit wählen mit Doppelpunkt
    # --------------------------------------------------
    def select_start_time(self):
        self.select_time(self.start_time_var, "Startzeit")

    def select_end_time(self):
        self.select_time(self.end_time_var, "Endzeit")

    def select_time(self, variable, title):
        top = tk.Toplevel(self.root)
        top.title(title)

        time_frame = ttk.Frame(top)
        time_frame.pack(padx=10, pady=10)

        ttk.Label(time_frame, text="Stunde (00-23):").grid(row=0, column=0, padx=5, pady=5)
        hour_var = tk.StringVar()
        hour_entry = ttk.Entry(time_frame, textvariable=hour_var, width=2)
        hour_entry.grid(row=0, column=1, padx=2, pady=5)

        ttk.Label(time_frame, text=":").grid(row=0, column=2, padx=2, pady=5)

        ttk.Label(time_frame, text="Minute (00-59):").grid(row=0, column=3, padx=5, pady=5)
        minute_var = tk.StringVar()
        minute_entry = ttk.Entry(time_frame, textvariable=minute_var, width=2)
        minute_entry.grid(row=0, column=4, padx=2, pady=5)

        def confirm_time(event=None):
            h = hour_var.get()
            m = minute_var.get()

            if len(h) != 2 or len(m) != 2:
                handle_error("Bitte exakt 2 Ziffern für Stunde und Minute eingeben.", self.message_label)
                return
            if not (h.isdigit() and m.isdigit()):
                handle_error("Nur Ziffern sind erlaubt (z.B. 07:05).", self.message_label)
                return

            hour_int = int(h)
            minute_int = int(m)
            if not (0 <= hour_int <= 23):
                handle_error("Stunde muss zwischen 00 und 23 liegen.", self.message_label)
                return
            if not (0 <= minute_int <= 59):
                handle_error("Minute muss zwischen 00 und 59 liegen.", self.message_label)
                return

            time_str = f"{h}:{m}"
            variable.set(time_str)
            top.destroy()

        top.bind("<Return>", confirm_time)
        hour_entry.focus()

    # --------------------------------------------------
    # 1) Karte für STARTPUNKT
    # --------------------------------------------------
    def open_map_for_startpoint(self, event=None):
        self.open_map_generic(
            var_name="start_point",
            window_title="Startpunkt wählen",
            confirm_btn_text="Diesen Startpunkt übernehmen"
        )

    # --------------------------------------------------
    # 2) Karte für ENDPUNKT
    # --------------------------------------------------
    def open_map_for_endpoint(self, event=None):
        self.open_map_generic(
            var_name="end_point",
            window_title="Endpunkt wählen",
            confirm_btn_text="Diesen Endpunkt übernehmen"
        )

    # --------------------------------------------------
    # ABSTRAKTE HILFSFUNKTION: Offene Karte (für Start + End)
    # --------------------------------------------------
    def open_map_generic(self, var_name, window_title, confirm_btn_text):
        map_window = tk.Toplevel(self.root)
        map_window.title(window_title)

        style = ttk.Style(map_window)
        style.configure(
            "BigButton.TButton",
            font=("Arial", 12, "bold"),
            padding=6
        )

        search_frame = ttk.Frame(map_window)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        def search_location():
            nonlocal marker
            query = search_var.get().strip()
            if not query:
                return
            if marker is not None:
                handle_error("Ein Marker existiert bereits. Bitte 'Marker zurücksetzen'.", self.message_label)
                return

            try:
                loc = geolocator.geocode(query)
                if loc:
                    map_widget.set_position(loc.latitude, loc.longitude)
                    map_widget.set_zoom(14)
                    marker = map_widget.set_marker(loc.latitude, loc.longitude, text="")
                    marker.set_marker_color("red")
                    disable_left_click()
                else:
                    handle_error("Adresse nicht gefunden.", self.message_label)
            except Exception as e:
                handle_error(f"Fehler bei der Ortssuche: {e}", self.message_label)

        search_button = ttk.Button(search_frame, text="Suchen", command=search_location)
        search_button.pack(side=tk.LEFT, padx=5)

        action_frame = ttk.Frame(map_window)
        action_frame.pack(fill=tk.X, padx=5, pady=5)

        map_widget = TkinterMapView(map_window, width=800, height=600, corner_radius=0)
        map_widget.set_tile_server(
            f"https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{{z}}/{{x}}/{{y}}?access_token={MAPBOX_API_KEY}",
            tile_size=512,
            max_zoom=19
        )

        # Standard-Position: Karlsruhe
        karlsruhe_lat, karlsruhe_lon = 49.00937, 8.40444
        map_widget.set_position(karlsruhe_lat, karlsruhe_lon)
        map_widget.set_zoom(12)

        marker = None

        def disable_left_click():
            map_widget.remove_left_click_map_command(on_map_click)

        def enable_left_click():
            map_widget.add_left_click_map_command(on_map_click)

        def on_map_click(coordinate):
            nonlocal marker
            if marker is not None:
                handle_error("Ein Marker existiert bereits. Bitte 'Marker zurücksetzen'.", self.message_label)
                return
            lat, lon = coordinate
            marker = map_widget.set_marker(lat, lon, text="")
            marker.set_marker_color("red")
            disable_left_click()

        enable_left_click()

        def reset_marker():
            nonlocal marker
            if marker:
                marker.delete()
                marker = None
            enable_left_click()

        def confirm_selection():
            if marker:
                lat, lon = marker.position
                coord_str = f"{lat:.5f}, {lon:.5f}"
                if var_name == "start_point":
                    self.start_point_var.set(coord_str)
                else:
                    self.end_point_var.set(coord_str)
            map_window.destroy()

        reset_btn = ttk.Button(
            action_frame,
            text="Marker zurücksetzen",
            command=reset_marker,
            style="BigButton.TButton"
        )
        reset_btn.pack(side=tk.LEFT, padx=10)

        confirm_btn = ttk.Button(
            action_frame,
            text=confirm_btn_text,
            command=confirm_selection,
            style="BigButton.TButton"
        )
        confirm_btn.pack(side=tk.RIGHT, padx=10)

        map_widget.pack(fill=tk.BOTH, expand=True)

    # --------------------------------------------------
    # Speichern und Validierung
    # --------------------------------------------------
    def save_entry(self):
        user = self.user_var.get()
        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()
        start_time = self.start_time_var.get()
        end_time = self.end_time_var.get()
        start_point = self.start_point_var.get()
        end_point = self.end_point_var.get()
        mode = self.mode_var.get()
        purpose = self.purpose_var.get()

        if not all([user, start_date, start_time, end_date, end_time, start_point, end_point, mode, purpose]):
            handle_error("Bitte alle Felder ausfüllen.", self.message_label)
            return

        start_datetime_str = f"{start_date} {start_time}"
        end_datetime_str = f"{end_date} {end_time}"

        dist = calculate_distance(start_point, end_point)
        if dist is None:
            handle_error("Distanz konnte nicht berechnet werden.", self.message_label)
            return

        entry = {
            "Benutzer/in": user,
            "Startdatum": start_date,
            "Startzeit": start_time,
            "Enddatum": end_date,
            "Endzeit": end_time,
            "Startzeit_kombiniert": start_datetime_str,
            "Endzeit_kombiniert": end_datetime_str,
            "Startpunkt": start_point,
            "Endpunkt": end_point,
            "Distanz (km)": dist,
            "Modus": mode,
            "Wegezweck": purpose,
        }
        save_to_csv(entry, DATA_FILE)

        show_success("Der Eintrag wurde erfolgreich abgespeichert.", self.message_label)
        self.clear_fields()

    def clear_fields(self):
        self.user_menu.set("")
        self.start_date_var.set("")
        self.end_date_var.set("")
        self.start_time_var.set("")
        self.end_time_var.set("")
        self.start_point_var.set("")
        self.end_point_var.set("")
        self.mode_var.set("")
        self.purpose_var.set("")

    def clear_message(self, *args):
        self.message_label.config(text="")

    def reset_all(self):
        self.user_menu.set("")
        if os.path.exists(USER_FILE):
            os.remove(USER_FILE)
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        self.load_users()
        self.clear_fields()
        self.message_label.config(text="")

    # --------------------------------------------------
    # Analyse und Diagramme
    # --------------------------------------------------
    def analyze_data(self):
        df = load_csv(DATA_FILE)
        if df is None or df.empty:
            handle_error("Keine Daten zum Auswerten vorhanden.", self.message_label)
            return

        # Optional sicherstellen, dass "Distanz (km)" wirklich numerisch ist
        df["Distanz (km)"] = pd.to_numeric(df["Distanz (km)"], errors="coerce")

        create_chart_directory()

        # 1) Modal Split (Wege in %)
        ways_by_mode_percent = df["Modus"].value_counts(normalize=True) * 100
        ways_chart_path = os.path.join(CHART_DIRECTORY, "modal_split_ways.png")

        plt.figure(figsize=(5, 5))
        ways_by_mode_percent.plot(
            kind="pie", autopct="%.1f%%", startangle=140
        )
        plt.title("Modal Split (Anzahl Wege in %)")
        plt.ylabel("")
        plt.tight_layout()
        plt.savefig(ways_chart_path)
        plt.close()

        # 2) Modal Split (Kilometer in %)
        km_sum_by_mode = df.groupby("Modus")["Distanz (km)"].sum()
        total_km = km_sum_by_mode.sum()
        if total_km == 0:
            handle_error("Keine Distanz vorhanden, Diagramm kann nicht erstellt werden.", self.message_label)
            return

        km_by_mode_percent = (km_sum_by_mode / total_km) * 100
        km_chart_path = os.path.join(CHART_DIRECTORY, "modal_split_km.png")

        plt.figure(figsize=(5, 5))
        km_by_mode_percent.plot(
            kind="pie", autopct="%.1f%%", startangle=140
        )
        plt.title("Modal Split (Kilometer in %)")
        plt.ylabel("")
        plt.tight_layout()
        plt.savefig(km_chart_path)
        plt.close()

        analysis_window = tk.Toplevel(self.root)
        analysis_window.title("Analyse Ergebnisse: Modal Split")

        try:
            ways_img = Image.open(ways_chart_path)
            ways_photo = ImageTk.PhotoImage(ways_img)
            ways_label = tk.Label(analysis_window, image=ways_photo)
            ways_label.image = ways_photo
            ways_label.pack(side=tk.LEFT, padx=10, pady=10)

            km_img = Image.open(km_chart_path)
            km_photo = ImageTk.PhotoImage(km_img)
            km_label = tk.Label(analysis_window, image=km_photo)
            km_label.image = km_photo
            km_label.pack(side=tk.LEFT, padx=10, pady=10)

        except Exception as e:
            handle_error(f"Fehler beim Laden der Diagramme: {e}", self.message_label)
            return

        show_success("Auswertung erfolgreich abgeschlossen.", self.message_label)

# --------------------------------------------------
# Hauptprogramm starten
# --------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = TrafficDiaryApp(root)
    root.mainloop()