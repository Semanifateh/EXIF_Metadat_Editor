import streamlit as st  # Import de Streamlit pour la création de l'interface utilisateur web
from PIL import Image  # Import de Pillow pour ouvrir et manipuler les images
import exifread  # Import de exifread pour lire les métadonnées EXIF des images
import folium  # Import de Folium pour créer des cartes interactives
from streamlit_folium import st_folium  # Import de st_folium pour intégrer Folium avec Streamlit
import piexif  # Import de piexif pour manipuler les données EXIF des images
from geopy.geocoders import Nominatim  # Import de Nominatim pour le géocodage (conversion de lieu en coordonnées GPS)
from geopy.exc import GeocoderTimedOut, GeocoderServiceError  # Import des exceptions pour gérer les erreurs de géocodage

# Fonction pour afficher l'image et ses métadonnées EXIF
def display_image_and_metadata(image_path):
    """
    Affiche l'image et ses métadonnées EXIF à partir du chemin de l'image donné.
    """
    image = Image.open(image_path)  # Ouverture de l'image à partir du chemin fourni
    st.image(image, caption='Image', use_column_width=True)  # Affichage de l'image dans Streamlit avec un titre

    # Lecture des métadonnées EXIF de l'image
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f)  # Extraction des métadonnées EXIF

    st.write("EXIF Metadata:")  # Affichage d'un titre pour les métadonnées EXIF
    for tag in tags.keys():  # Parcours de toutes les balises EXIF
        st.write(f"{tag}: {tags[tag]}")  # Affichage de chaque balise et sa valeur

# Fonction pour modifier les données EXIF de l'image
def edit_exif_data(image_path, new_exif):
    """
    Modifie les données EXIF de l'image en fonction des nouvelles valeurs fournies.
    """
    image = Image.open(image_path)  # Ouverture de l'image
    exif_dict = piexif.load(image.info['exif'])  # Chargement des données EXIF existantes

    # Mise à jour des données EXIF avec les nouvelles coordonnées GPS
    if 'GPSLatitude' in new_exif and 'GPSLongitude' in new_exif:
        try:
            lat = float(new_exif['GPSLatitude'])
            lon = float(new_exif['GPSLongitude'])

            # Fonction pour convertir les coordonnées en format rationnel EXIF
            def to_rational(val):
                d = int(val)
                m = int((val - d) * 60)
                s = (val - d - m / 60) * 3600
                return (d, 1), (m, 1), (int(s * 100), 100)

            # Mise à jour des valeurs GPS dans les métadonnées EXIF
            exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = to_rational(lat)
            exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = to_rational(lon)
            exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = 'N' if lat >= 0 else 'S'
            exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = 'E' if lon >= 0 else 'W'

        except ValueError:
            st.write("Invalid GPS coordinates")  # Affichage d'un message d'erreur si les coordonnées GPS sont invalides

    # Conversion des données EXIF mises à jour en format binaire
    exif_bytes = piexif.dump(exif_dict)
    # Sauvegarde de l'image avec les nouvelles métadonnées EXIF dans un nouveau fichier
    image.save("edited_" + image_path, exif=exif_bytes)

# Fonction pour obtenir les coordonnées GPS à partir d'un nom de lieu et d'un pays
def geocode_location(place, country):
    """
    Obtient les coordonnées GPS d'un lieu donné dans un pays spécifique en utilisant Nominatim.
    """
    geolocator = Nominatim(user_agent="streamlit-exif-editor")  # Initialisation du géocodeur Nominatim
    try:
        location = geolocator.geocode(f"{place}, {country}")  # Géocodage du lieu
        if location:
            return location.latitude, location.longitude  # Retourne les coordonnées GPS si trouvées
        else:
            st.warning(f"Could not geocode location: {place}, {country}")  # Avertissement si le lieu ne peut pas être géocodé
            return None, None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        st.error(f"Geocoding error: {e}")  # Affichage d'un message d'erreur en cas de problème de géocodage
        return None, None

# Fonction principale pour exécuter l'application Streamlit
def main():
    """
    Fonction principale pour exécuter l'application Streamlit.
    """
    st.title("EXIF Metadata Editor")  # Titre de la page de l'application

    # Chargement du fichier image depuis l'interface utilisateur
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Sauvegarde de l'image téléchargée localement
        with open("uploaded_image.jpg", "wb") as f:
            f.write(uploaded_file.getbuffer())

        display_image_and_metadata("uploaded_image.jpg")  # Affichage de l'image et de ses métadonnées EXIF

        st.sidebar.title("Edit EXIF Metadata")  # Titre de la section de la barre latérale pour l'édition des métadonnées EXIF

        # Champs de saisie pour les nouvelles coordonnées GPS
        gps_lat = st.sidebar.text_input("GPS Latitude")
        gps_lon = st.sidebar.text_input("GPS Longitude")

        # Bouton pour mettre à jour les données EXIF de l'image
        if st.sidebar.button("Update EXIF"):
            new_exif = {  # Dictionnaire avec les nouvelles valeurs EXIF
                'GPSLatitude': gps_lat,
                'GPSLongitude': gps_lon,
            }
            edit_exif_data("uploaded_image.jpg", new_exif)  # Mise à jour des données EXIF
            st.success("EXIF data updated successfully!")  # Message de succès

        st.subheader("Carte des coordonnées GPS")
        if gps_lat and gps_lon and gps_lat != "0" and gps_lon != "0":
            try:
                lat = float(gps_lat)
                lon = float(gps_lon)
                # Création d'une carte centrée sur les coordonnées GPS fournies
                m = folium.Map(location=[lat, lon], zoom_start=15)
                folium.Marker([lat, lon], tooltip="Nouvelle position").add_to(m)  # Ajout d'un marqueur sur la carte
                st_folium(m, width=700, height=500)  # Affichage de la carte dans l'application Streamlit
            except ValueError:
                st.write("Veuillez entrer des coordonnées GPS valides.")  # Message d'erreur si les coordonnées GPS sont invalides
        else:
            st.write("Veuillez entrer des coordonnées GPS valides.")

    # Section pour ajouter des Points of Interest (POI)
    st.sidebar.title("Ajouter des POI (Points of Interest)")
    poi_place = st.sidebar.text_input("Nom du lieu")  # Champ de saisie pour le nom du lieu
    poi_country = st.sidebar.text_input("Pays")  # Champ de saisie pour le pays

    # Initialisation de la liste des POI dans l'état de session si elle n'existe pas encore
    if 'poi_list' not in st.session_state:
        st.session_state['poi_list'] = []

    # Bouton pour ajouter un POI
    if st.sidebar.button("Ajouter POI"):
        if poi_place and poi_country:
            lat, lon = geocode_location(poi_place, poi_country)  # Obtention des coordonnées GPS du POI
            if lat is not None and lon is not None:
                # Ajout du POI à la liste
                st.session_state['poi_list'].append({'lat': lat, 'lon': lon, 'name': poi_place})
                st.success(f"POI '{poi_place}' ajouté!")  # Message de succès
        else:
            st.error("Veuillez remplir tous les champs pour ajouter un POI.")  # Message d'erreur si les champs ne sont pas tous remplis

    # Affichage de la carte des POI si la liste des POI n'est pas vide
    if st.session_state['poi_list']:
        st.subheader("Carte des POI")
        # Création d'une carte centrée sur une position par défaut
        m = folium.Map(location=[0, 0], zoom_start=2)

        # Ajout des marqueurs pour chaque POI sur la carte
        for poi in st.session_state['poi_list']:
            folium.Marker([poi['lat'], poi['lon']], tooltip=poi['name']).add_to(m)

        # Ajout de lignes entre les POI pour visualiser les trajets ou connexions
        points = [(poi['lat'], poi['lon']) for poi in st.session_state['poi_list']]
        folium.PolyLine(points, color="blue").add_to(m)

        st_folium(m, width=700, height=500)  # Affichage de la carte des POI dans l'application Streamlit

# Point d'entrée pour exécuter le script
if __name__ == "__main__":
    main()  # Exécution de la fonction principale pour lancer l'application
