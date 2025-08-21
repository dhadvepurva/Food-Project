import streamlit as st 
import sqlite3
import pandas as pd 
import matplotlib.pyplot as plt 


# Database Connection

conn = sqlite3.connect("food_waste.db") 
st.set_page_config(page_title="Food Wastage Management", layout="wide")
st.title(" Local Food Wastage Management System")
st.markdown(""" 
### Welcome to the Local Food Wastage Management System.
This app helps analyze food providers, receivers, claims, and donations.
It also allows performing CRUD operations on food listing.
""")


# Tabs for 4 Groups

tab1, tab2, tab3, tab4 = st.tabs([
    "Providers & Receivers", 
    "Food Listings & Availability", 
    "Claims & Distribution", 
    "Analysis & Insights"
])

# 1. Providers & Receivers

with tab1:
    st.header("🏢 Providers & Receivers")

    # Q1. Providers & Receivers per City
    st.subheader("1️⃣ Providers and Receivers per City")
    # providers count per city
    df_city = pd.read_sql_query("""
        SELECT 
            COALESCE(p.City, r.City) AS City,
            COUNT(DISTINCT p.Provider_ID) AS providers,
            COUNT(DISTINCT r.Receiver_ID) AS receivers
        FROM providers p
        LEFT JOIN receivers r ON p.City = r.City
        GROUP BY COALESCE(p.City, r.City)

        UNION

        SELECT 
            COALESCE(p.City, r.City) AS City,
            COUNT(DISTINCT p.Provider_ID) AS providers,
            COUNT(DISTINCT r.Receiver_ID) AS receivers
        FROM receivers r
        LEFT JOIN providers p ON p.City = r.City
        GROUP BY COALESCE(p.City, r.City)

        ORDER BY City;
    """, conn)

    
    st.dataframe(df_city)


    st.markdown(" ** insight:** This shows which cities have the most providers and receivers."
                "It helps balance supply and demand - if receivers are high but providers are low, more donations are needed there.")
    

    # Q2. Provider types contribution
    st.subheader("2️⃣ Which provider type contributes most?")
    df_types = pd.read_sql_query("""
        SELECT Provider_Type, COUNT(*) AS Total
        FROM food_listing
        GROUP BY Provider_Type
        Order BY Total DESC
    """, conn)
    st.bar_chart(df_types.set_index("Provider_Type"))
    st.markdown(" **Insights:** Identifying which type of provider(e.g., restaurants or stores) contributes most helps recognize key donors"
                "and encourage other types to participate more")

    # Q3. Provider contacts in a city
    st.subheader("3️⃣ Provider contact info by city")
    city_filter = st.text_input("Enter City Name:")
    if city_filter:
        df_contacts = pd.read_sql_query(
            "SELECT Name, Contact FROM providers WHERE City = ?", 
            conn, params=(city_filter,)
        )
        st.table(df_contacts)
        st.markdown(" **Insights** Listing provider contact details makes it easier for receivers or NGOs to directly reach donors in their city")

    # Q4. Top Receivers by claims
    st.subheader("4️⃣ Receivers with most food claims")
    df_receivers = pd.read_sql_query("""
        SELECT r.Name, COUNT(c.Claim_ID) AS Total_Claims
        FROM claims c
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
        GROUP BY r.Name
        ORDER BY Total_Claims DESC
        LIMIT 5
    """, conn)
    st.dataframe(df_receivers)
    st.markdown(" **Insights:** The most active receivers can be identified here."
                "They may represent communities or NGOs that need extra support.")


# 2. Food Listings & Availability

with tab2:
    st.header("🥗 Food Listings & Availability")

    # Q5. Total quantity available
    st.subheader("5️⃣ Total food available")
    total_qty = pd.read_sql_query(
        "SELECT SUM(Quantity) as Total FROM food_listing", conn
    )["Total"][0]
    st.metric("Total Quantity Available", total_qty)
    st.markdown(" **Insights:** The total available quantity gives an idea of how much food is ready to be redistributed at any time.")

    # Q6. City with most listings
    st.subheader("6️⃣ City with most food listings")
    df_city_listings = pd.read_sql_query("""
        SELECT Location, COUNT(*) AS Listings
        FROM food_listing
        GROUP BY Location
        ORDER BY Listings DESC
    """, conn)
    st.bar_chart(df_city_listings.set_index("Location"))

    # Show table below
    st.write("Claims Table:")
    st.dataframe(df_city_listings)
    st.markdown(" **Insights:** The city with most listings shows where donor activity is strongest."
                "Other cities with fewer listings may need more awareness campaigns.")

    # Q7. Most common food types
    st.subheader("7️⃣ Most common food types")
    df_food_types = pd.read_sql_query("""
        SELECT Food_Type, COUNT(*) AS Listings
        FROM food_listing
        GROUP BY Food_Type
        ORDER BY Listings DESC
    """, conn)
    st.dataframe(df_food_types.head(10))
    st.markdown(" **Insights:** Knowing the most available food types helps receivers plan meals and also shows donation trends(e.g., vegetables,rice).")


# 3. Claims & Distribution

with tab3:
    st.header("📦 Claims & Distribution")

    # Q8. Claims per food item
    st.subheader("8️⃣ Claims per food item")
    df_claims = pd.read_sql_query("""
        SELECT fl.Food_Name, COUNT(c.Claim_ID) AS Total_Claims
        FROM food_listing fl
        LEFT JOIN claims c ON fl.Food_ID = c.Food_ID
        GROUP BY fl.Food_Name
        ORDER BY Total_Claims DESC
    """, conn)
    # Show table
    st.dataframe(df_claims)

    # Show pie chart with smaller figure size
    fig, ax = plt.subplots(figsize=(3,3))
    ax.pie(df_claims["Total_Claims"], labels=df_claims["Food_Name"], autopct="%1.1f%%")
    ax.set_title("Claims per food item", fontsize=12)
    st.pyplot(fig)

    st.markdown(" **Insights:** Food items with the most claims are in highest demand."
                "This can guide providers on what food is most useful for donations.")

    # Q9. Provider with most successful claims
    st.subheader("9️⃣ Provider with most successful claims")
    df_provider_success = pd.read_sql_query("""
        SELECT p.Name, COUNT(*) AS Successful_Claims
        FROM claims c
        JOIN food_listing fl ON c.Food_ID = fl.Food_ID
        JOIN providers p ON fl.Provider_ID = p.Provider_ID
        WHERE LOWER(c.Status) = 'completed'
        GROUP BY p.Name
        ORDER BY Successful_Claims DESC
        LIMIT 1
    """, conn)
    st.table(df_provider_success)
    st.markdown(" **Insights:** This shows which provider makes the biggest impact."
                "They can be rewarded or recognized as role models for other donors.")

    # Q10. Claim status distribution
    st.subheader("🔟 Claim status distribution")
    df_status = pd.read_sql_query("""
        SELECT Status, COUNT(*) AS Count
        FROM claims
        GROUP BY Status
    """, conn)
    fig, ax = plt.subplots()
    ax.pie(df_status["Count"], labels=df_status["Status"], autopct="%1.1f%%")
    st.pyplot(fig)
    st.markdown(" **Insights:** The share of completed vs. pending vs. cancelled claims helps track system efficiency."
                "A high pending/cancelled rate may delays or mismatches in supply-demand.")


# 4. Analysis & Insights

with tab4:
    st.header("📊 Analysis & Insights")

    # Q11. Avg claimed per receiver
    st.subheader("1️⃣1️⃣ Average quantity claimed per receiver")
    df_avg_claim = pd.read_sql_query("""
        SELECT r.Name, ROUND(AVG(fl.Quantity),2) AS Avg_Quantity
        FROM claims c
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
        JOIN food_listing fl ON c.Food_ID = fl.Food_ID
        GROUP BY r.Name
    """, conn)
    st.dataframe(df_avg_claim)
    st.markdown(" **Insight:** Some receivers claim larger quantities than others. "
            "This indicates where the need is greatest and helps manage fair distribution.")


    # Q12. Meal type claimed most
    st.subheader("1️⃣2️⃣ Most claimed meal type")
    df_meals = pd.read_sql_query("""
        SELECT fl.Meal_Type, COUNT(*) AS Total_Claims
        FROM claims c
        JOIN food_listing fl ON c.Food_ID = fl.Food_ID
        GROUP BY fl.Meal_Type
        ORDER BY Total_Claims DESC
    """, conn)
    # Chart
    st.bar_chart(df_meals.set_index("Meal_Type"))

    # Table
    st.write("Detaild Data:")
    st.dataframe(df_meals)
    st.markdown(" **Insight:** If dinner is claimed most, it suggests receivers prioritize evening meals. "
            "This helps providers plan which meals to donate more often.")


    # Q13. Total donated by provider
    st.subheader("1️⃣3️⃣ Total donated food by provider")
    df_donated = pd.read_sql_query("""
        SELECT p.Name, SUM(fl.Quantity) AS Total_Donated
        FROM food_listing fl
        JOIN providers p ON fl.Provider_ID = p.Provider_ID
        GROUP BY p.Name
        ORDER BY Total_Donated DESC
    """, conn)
    st.dataframe(df_donated.head(10))
    st.markdown(" **Insight:** This shows which providers donate the most food overall. "
            "It highlights top contributors and inspires others to increase their donations.")
    
    # 5. CRUD Operations

    crud_tab = st.sidebar.radio(" CRUD Menu", ["Create", "Read"," Update", "Delete"])

    st.header("CRUD Operations")

    # CREATE
    if crud_tab == "Create":
        st.subheader("Add New Food Listing")
        with st.form("add_food"):
            food_id = st.number_input("Food ID", min_value=1, step=1)
            food_name = st.text_input("Food Name")
            qty = st.number_input("Quantity", min_value=1, step=1) 
            expiry = st.date_input("Expiry Date")
            provider_id = st.number_input("Provider ID", min_value=1, step=1)
            provider_type = st.text_input("Provider Type")
            location = st.text_input("Location")
            food_type = st.text_input("Food Type")
            meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])
            submitted = st.form_submit_button("Add Food")
            if submitted:
                conn.execute("""
                    INSERT INTO food_listing (Food_ID, Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (food_id, food_name, qty, expiry, provider_id, provider_type, location, food_type, meal_type))
                conn.commit()
                st.success("New food listing added!")

    # READ
    elif crud_tab == "Read":
        st.subheader("View food Listing")
        df_all = pd.read_sql_query("SELECT * FROM food_listing", conn)
        st.dataframe(df_all)

        st.subheader("View Claim by ID")
        claim_id = st.number_input("Enter Claim ID", min_value=1, step=1)
        if st.button("Fetch Claim"):
            query = "SELECT * FROM Claims WHERE Claim_ID = ?"
            df_claim = pd.read_sql_query(query, conn, params=(claim_id,))

            if not df_claim.empty:
                st.dataframe(df_claim)
            else:
                st.warning(f"No claim found with Claim_ID {claim_id}") 


    # UPDATE
    elif crud_tab == "Update":
        st.subheader("Update Claim Status")

        claim_id = st.number_input("Enter Claim ID", min_value=1, step=1)
        new_status = st.selectbox("New Status", ["Pending", "Completed", "Cancelled"])

        if st.button("Update Claim"):
           query = ("UPDATE claims SET Status = ? WHERE Claim_ID= ?", (new_status, claim_id))
           df_claim = pd.read_sql_query(query, params=(new_status, claim_id))



                

        

                
    # DELETE
    elif crud_tab == "Delete":
        st.subheader("Delete Food Listing")
        del_id = st.number_input("Enter Food ID to delete", min_value=1,step=1)
        if st.button("Delete"):
            conn.execute("DELETE FROM food_listing WHERE Food_ID = ?",(del_id,))
            conn.commit()
            st.warning(f"Food listing {del_id} deleted successfully!")



            