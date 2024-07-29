import streamlit as st  # Import de la bibliothèque Streamlit pour créer l'interface utilisateur web.
from PIL import Image  # Import de la bibliothèque Pillow pour manipuler les images.
import exifread  # Import de la bibliothèque exifread pour lire les métadonnées EXIF des images.
import folium  # Import de la bibliothèque folium pour afficher des cartes interactives.
from streamlit_folium import st_folium  # Import de la fonction st_folium pour intégrer Folium avec Streamlit.
import piexif  # Import de la bibliothèque piexif pour manipuler les données EXIF.

# Fonction pour afficher l'image et ses métadonnées EXIF
def display_image_and_metadata(image_path):
    image = Image.open(image_path)  # Ouverture de l'image à partir du chemin donné.
    st.image(image, caption='Image', use_column_width=True)  # Affichage de l'image dans l'application Streamlit avec un titre.
    
    with open(image_path, 'rb') as f:  # Ouverture du fichier image en mode binaire pour lire les métadonnées EXIF.
        tags = exifread.process_file(f)  # Extraction des métadonnées EXIF de l'image.
    
    st.write("EXIF Metadata:")  # Affichage d'un titre pour les métadonnées EXIF.
    for tag in tags.keys():  # Parcours des balises EXIF.
        st.write(f"{tag}: {tags[tag]}")  # Affichage de chaque balise et sa valeur.

# Fonction pour modifier les données EXIF de l'image
def edit_exif_data(image_path, new_exif):
    image = Image.open(image_path)  # Ouverture de l'image.
    exif_dict = piexif.load(image.info['exif'])  # Chargement des données EXIF existantes.
    
    # Mise à jour des données EXIF
    if 'GPSLatitude' in new_exif and 'GPSLongitude' in new_exif:
        try:
            lat = float(new_exif['GPSLatitude'])
            lon = float(new_exif['GPSLongitude'])
            
            # Convertir latitude et longitude en format EXIF
            def to_rational(val):
                d = int(val)
                m = int((val - d) * 60)
                s = (val - d - m / 60) * 3600
                return (d, 1), (m, 1), (int(s * 100), 100)

            exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = to_rational(lat)
            exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = to_rational(lon)
            exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = 'N' if lat >= 0 else 'S'
            exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = 'E' if lon >= 0 else 'W'

        except ValueError:
            st.write("Invalid GPS coordinates")

    # Conversion des données EXIF en format binaire
    exif_bytes = piexif.dump(exif_dict)
    
    # Sauvegarde de l'image avec les nouvelles métadonnées EXIF dans un nouveau fichier
    image.save("edited_" + image_path, exif=exif_bytes)

# Fonction principale pour exécuter l'application Streamlit
def main():
    st.title("EXIF Metadata Editor")  # Définir le titre de la page de l'application Streamlit.
    
    # Chargement du fichier image depuis l'interface utilisateur.
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:  # Si un fichier image a été téléchargé.
        with open("uploaded_image.jpg", "wb") as f:  # Ouverture d'un fichier en mode écriture binaire pour sauvegarder l'image téléchargée.
            f.write(uploaded_file.getbuffer())  # Écriture du contenu du fichier téléchargé dans le fichier local.
        
        display_image_and_metadata("uploaded_image.jpg")  # Afficher l'image et ses métadonnées EXIF.
        
        st.sidebar.title("Edit EXIF Metadata")  # Définir le titre de la section de la barre latérale pour l'édition des métadonnées EXIF.
        
        gps_lat = st.sidebar.text_input("GPS Latitude")  # Champ de saisie pour la latitude GPS dans la barre latérale.
        gps_lon = st.sidebar.text_input("GPS Longitude")  # Champ de saisie pour la longitude GPS dans la barre latérale.
        
        if st.sidebar.button("Update EXIF"):  # Bouton pour appliquer les nouvelles données EXIF.
            new_exif = {  # Création d'un dictionnaire avec les nouvelles valeurs EXIF.
                'GPSLatitude': gps_lat,
                'GPSLongitude': gps_lon,
            }
            edit_exif_data("uploaded_image.jpg", new_exif)  # Mise à jour des données EXIF de l'image avec les nouvelles valeurs.
            st.success("EXIF data updated successfully!")  # Affichage d'un message de succès.

        # Afficher la carte avec les nouvelles coordonnées GPS
        st.subheader("Carte des coordonnées GPS")
        if gps_lat and gps_lon and gps_lat != "0" and gps_lon != "0":
            try:
                lat = float(gps_lat)
                lon = float(gps_lon)
                m = folium.Map(location=[lat, lon], zoom_start=15)
                folium.Marker([lat, lon], tooltip="Nouvelle position").add_to(m)
                st_folium(m, width=700, height=500)
            except ValueError:
                st.write("Veuillez entrer des coordonnées GPS valides.")
        else:
            st.write("Veuillez entrer des coordonnées GPS valides.")

if __name__ == "__main__":  # Si ce fichier est exécuté directement (pas importé comme module).
    main()  # Exécution de la fonction principale pour lancer l'application Streamlit.
