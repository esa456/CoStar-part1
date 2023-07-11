"""
This file focuses on part1 of the CoStar coding challenge and highlights the functions used
to ascertain the output provided by the CoStar team
"""
############################################################################################
import re
import json
from datetime import date
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


############################################################################################
def emulate_browser():
    """This function instantiates the browser"""

    options = Options()
    options.add_argument("--headless")
    browser = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    return browser


############################################################################################
def details_collection(link):
    """This function pools together all necessary information scraped from webpage """

    # Instantiate browser
    browser = emulate_browser()

    # Retrieve webpage
    browser.get(link)

    # Get the current timestamp
    current_time = date.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")

    # Before switching to iframe gather 'country' and 'language'
    basic_info = browser.find_element(By.XPATH, "/html").get_attribute("lang")
    basic_properties = basic_info.split("-")

    # Switch to iframe
    iframe = browser.find_element(By.XPATH, '//*[@id="buildout"]/iframe')
    browser.switch_to.frame(iframe)

    # Retrieve 'transaction_type', 'address', 'sale_or_rent' and 'building_name' info
    property_info = overview(browser)

    # Retrieve 'latitude' and 'longitude' information
    coordinates_list = coordinates(browser)

    # Retrieve the description which holds 'sale_stage' information
    description_content = description(browser)

    # Retrieve the property details which holds 'building_type' and 'size' info
    property_content = property_details(browser)

    # Retrieve 'contacts' info
    brokers = contacts_filter(browser)

    # Retrieve 'brochure_link' info
    files = documents(browser)

    # Retrieve 'spaces' info
    spaces_content = spaces(browser)

    # Specifically retrieve 'building_type' from property details
    building_type = (
        extract_data_from_list(property_content, "Property Type") + " Building"
    )

    # Specifically retrieve 'size' from property details
    size = extract_data_from_list(property_content, "Size")

    # Specifically retrieve 'sale_stage' from description information
    sale_stage = extract_data_from_list(description_content, "Lease Term")

    # All data will be added to this dictionary
    output_dict = {
        "scraped_at": current_time,
        "address": property_info[1],
        "building_name": property_info[3],
        "latitude": coordinates_list[0],
        "longitude": coordinates_list[1],
        "url": link,
        "transaction_type": property_info[0],
        "sale_stage": sale_stage,
        "size": size,
        "building_type": building_type,
        "contacts": brokers,
        "sale_or_rent": property_info[2],
        "brochure_link": files,
        "spaces": spaces_content,
        "country": basic_properties[1].lower(),
        "language": basic_properties[0],
    }
    return output_dict


############################################################################################
def overview(browser):
    """This function retrieves transaction_type, building_name, address and
    sale_or_rent information"""

    # Find the main title element
    overview_data = browser.find_element(
        By.XPATH, "/html/body/div[3]/div[5]/div/div"
    ).text
    property_info = overview_data.split("\n")

    # transaction_type
    if "lease" in property_info[0]:
        property_info[0] = "for rent"

    # building_name
    building_name = property_info[1].split("|")
    property_info.append(building_name[0])

    # address
    property_info[1] = property_info[1].replace(" |", ",")

    # Sale or rent
    property_info[2] = "Lease Rate " + property_info[2]

    return property_info


############################################################################################
def coordinates(browser):
    """This function retrieves the latitude and longitude information"""

    coordinates_list = []

    # Look for the map section
    coordinates_data = browser.find_element(By.XPATH, '//*[@id="map"]').get_attribute(
        "outerHTML"
    )

    # find coordinate elements
    latitude = re.findall(r'data-latitude="(.*?)"', coordinates_data)
    longitude = re.findall(r'data-longitude="(.*?)"', coordinates_data)

    # if latitude is not found try another way
    if len(latitude) == 0:
        latitude = re.findall(r'lat="(.*?)"', coordinates_data)

    coordinates_list.append(latitude[0])

    # if longitude is not found try another way
    if len(longitude) == 0:
        longitude = re.findall(r'lng="(.*?)"', coordinates_data)

    # Add results to a list
    coordinates_list.append(longitude[0])

    return coordinates_list


############################################################################################
def property_details(browser):
    """This function retrieves the details found in the property details section"""

    property_details_list = []

    # Look for property details section
    prop_details = browser.find_elements(
        By.CSS_SELECTOR, 'div[class="summary-table-split-item pr-sm-3"]'
    )

    # Loop through scraped info and append data to list
    for i in prop_details:
        property_details_list.append(i.text)

    return property_details_list


############################################################################################
def description(browser):
    """This function retrieves the details found in the description section"""

    description_list = []

    # Look for description section
    description_data = browser.find_element(
        By.XPATH, '//*[@id="overview"]/div/div[1]/div[3]'
    )
    description_elements = description_data.find_elements(By.CSS_SELECTOR, "p")

    # Loop through scraped info and append data to list
    for j in description_elements:
        description_list.append(j.text)

    return description_list


############################################################################################
def extract_data_from_list(description_list, filter_string):
    """This function extracts descriptive information from a list"""

    # Loop through elements in list
    for elem in description_list:

        # If the information we want appears in the element
        if filter_string in elem:

            # And it contains a : or \n
            if ":" in elem or "\n" in elem:

                # Split this element and retrieve the value (not the header)
                description_split = re.split(r":|\n", elem)
                description_value = description_split[-1].strip()

                # Look for the mention of availability
                if "available immediately" in description_value.lower():
                    description_value = "available"

            return description_value

    return None


############################################################################################
def contacts(browser):
    """This function retrieves the broker information"""

    brokers_details = []

    # Find the brokers section
    brokers = browser.find_element(By.CSS_SELECTOR, 'div[class="col-12 col-md-3"]')
    brokers_element = brokers.find_elements(By.CSS_SELECTOR, 'div[class="col-9 pl-3"]')

    # Loop through the scraped elements and add to list
    for i in brokers_element:
        brokers_details.append(i.text)

    return brokers_details


############################################################################################
def contacts_filter(browser):
    """This function filters and categorises the relevant broker information"""

    # Retrieve broker information
    contacts_list = contacts(browser)

    brokers_list = []

    # Loop through each broker
    for contact_details in contacts_list:

        # Split the data by \n
        details = contact_details.split("\n")

        telephone_list = []
        # Loop through the elements in details
        for deets in details:

            # Look for the existence of a colon
            if ":" in deets:

                # Extract only the digits from the string
                digits = re.sub(r"\D", "", deets)

                # Format the digits as 'tel:+1(XXX)XXX-XXXX'
                formatted_phone = f"tel:+1({digits[:3]}){digits[3:6]}{digits[6:]}"

                # Add to telephone list
                telephone_list.append(formatted_phone)

            # Look for the existence of an @
            if "@" in deets:

                email = deets

        # Add the results to a dictionary
        contact_dict = {"name": details[0], "telephone": telephone_list, "email": email}
        brokers_list.append(contact_dict)

    return brokers_list


############################################################################################
def documents(browser):
    """This function retrieves the brochure_links"""

    # Hosted in iframe so prefix is needed
    iframe_link_prefix = "https://buildout.com"

    link_list = []

    # Find the documents section and scrape data
    documents_section = browser.find_element(By.XPATH, '//*[@id="documents"]')
    links = documents_section.find_elements(By.CSS_SELECTOR, 'a[target="_blank"]')

    # Loop through scraped data, find relevant info and add to list
    for data in links:
        element = data.get_attribute("outerHTML")
        document_link = re.findall(r'href="(.*?)"', element)

        # Element added with prefix
        link_list.append(iframe_link_prefix + document_link[0])

    return link_list


############################################################################################
def spaces(browser):
    """This function retrieves the infomation found in the spaces section"""

    spaces_list = []

    # Find the spaces section and scrape data
    spaces_content = browser.find_element(By.XPATH, '//*[@id="spaces"]')
    table = spaces_content.find_elements(By.CSS_SELECTOR, 'div[class="card-body"]')

    # Loop through elements and gather relevant info
    for item in table:
        data = item.get_attribute("innerHTML")

        match = re.search(r"<h5>(.*?)</h5>", data)
        # Extract the match using the group() method
        if match:
            # Remove the <h5> tags using regular expressions
            clean_string = re.sub(r"<h5>|</h5>", "", match.group())
            spaces_dict = {"title": clean_string}

        else:
            # If a match isn't found populate title attribute with None
            spaces_dict = {"title": None}

        # Look for table content
        content = item.find_element(By.CSS_SELECTOR, 'div[class="row"]').get_attribute(
            "outerHTML"
        )

        # Retrieve headers and fields
        headers = re.findall(r"<th>(.*?)</th>", content)
        fields = re.findall(r"<td>(.*?)</td>", content)

        # Loop through both lists and match the corresponding headers and fields
        for header, field in zip(headers, fields):

            # filter for 'size' information
            if header == "Space Available":
                spaces_dict.update({"size": field})

            # filter for 'rent' information
            if header == "Lease Rate":
                spaces_dict.update({"rent": field})

        spaces_list.append(spaces_dict)

    return spaces_list


############################################################################################
def output(link):
    """This function gathers all our data and exports it to a json file"""

    # Retrieve all information in dictionary format
    output_dict = details_collection(link)

    # Convert dictionary to JSON formatted string with indentation for readability
    output_json = json.dumps(output_dict, indent=4)

    # Export this data to file
    with open("output.json", "w") as file:
        file.write(output_json)


############################################################################################
def main():
    """This is the main function"""


if __name__ == "__main__":

    LINK = "https://bradvisors.com/listings/?propertyId=842304-lease"

    output(LINK)
