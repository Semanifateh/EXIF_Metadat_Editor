import streamlit as st
from PIL import Image
import exifread
import folium
from streamlit_folium import st_folium
import piexif
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Fonction pour afficher l'image et ses métadonnées EXIF
def display_image_and_metadata(image_path):
    image = Image.open(image_path)
    st.image(image, caption='Image', use_column_width=True)
    
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f)
    
    st.write("EXIF Metadata:")
    for tag in tags.keys():
        st.write(f"{tag}: {tags[tag]}")

# Fonction pour modifier les données EXIF de l'image
def edit_exif_data(image_path, new_exif):
    image = Image.open(image_path)
    exif_dict = piexif.load(image.info['exif'])
    
    if 'GPSLatitude' in new_exif and 'GPSLongitude' in new_exif:
        try:
            lat = float(new_exif['GPSLatitude'])
            lon = float(new_exif['GPSLongitude'])
            
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

    exif_bytes = piexif.dump(exif_dict)
    image.save("edited_" + image_path, exif=exif_bytes)

# Fonction pour obtenir les coordonnées GPS à partir d'un nom de lieu et de pays
def geocode_location(place, country):
    geolocator = Nominatim(user_agent="streamlit-exif-editor")
    try:
        location = geolocator.geocode(f"{place}, {country}")
        if location:
            return location.latitude, location.longitude
        else:
            st.warning(f"Could not geocode location: {place}, {country}")
            return None, None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        st.error(f"Geocoding error: {e}")
        return None, None

# Fonction principale pour exécuter l'application Streamlit
def main():
    st.title("EXIF Metadata Editor")
    
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        with open("uploaded_image.jpg", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        display_image_and_metadata("uploaded_image.jpg")
        
        st.sidebar.title("Edit EXIF Metadata")
        
        gps_lat = st.sidebar.text_input("GPS Latitude")
        gps_lon = st.sidebar.text_input("GPS Longitude")
        
        if st.sidebar.button("Update EXIF"):
            new_exif = {
                'GPSLatitude': gps_lat,
                'GPSLongitude': gps_lon,
            }
            edit_exif_data("uploaded_image.jpg", new_exif)
            st.success("EXIF data updated successfully!")

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
    
    st.sidebar.title("Ajouter des POI (Points of Interest)")
    poi_place = st.sidebar.text_input("Nom du lieu")
    poi_country = st.sidebar.text_input("Pays")
    
    if 'poi_list' not in st.session_state:
        st.session_state['poi_list'] = []
    
    if st.sidebar.button("Ajouter POI"):
        if poi_place and poi_country:
            lat, lon = geocode_location(poi_place, poi_country)
            if lat is not None and lon is not None:
                st.session_state['poi_list'].append({'lat': lat, 'lon': lon, 'name': poi_place})
                st.success(f"POI '{poi_place}' ajouté!")
        else:
            st.error("Veuillez remplir tous les champs pour ajouter un POI.")
    
    if st.session_state['poi_list']:
        st.subheader("Carte des POI")
        m = folium.Map(location=[0, 0], zoom_start=2)
        
        for poi in st.session_state['poi_list']:
            folium.Marker([poi['lat'], poi['lon']], tooltip=poi['name']).add_to(m)
        
        # Ajouter des lignes entre les POI
        points = [(poi['lat'], poi['lon']) for poi in st.session_state['poi_list']]
        folium.PolyLine(points, color="blue").add_to(m)
        
        st_folium(m, width=700, height=500)

if __name__ == "__main__":
    main()

