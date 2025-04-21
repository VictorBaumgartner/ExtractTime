import re
import pandas as pd
from datetime import datetime, timedelta

def extract_date_and_time(text, date_publication=None):
    """
    Extracts dates and times from a given text and formats them for database insertion.

    Args:
        text (str): The text to extract dates and times from.
        date_publication (str, optional): Publication date if available. Defaults to None.

    Returns:
        list: A list of dictionaries, each containing formatted date and time information.
    """
    results = []

    # Date patterns
    date_patterns = [
        r"(\d{1,2})\s?(?:/|-|de|er|ème|eme)\s?(\d{1,2})\s?(?:/|-|de|er|ème|eme)\s?(\d{4})",  # 20/04/2025
        r"(\d{1,2})\s?(?:/|-|de|er|ème|eme)\s?(\w+)\s?(?:/|-|de|er|ème|eme)\s?(\d{4})",  # 20 avril 2025
        r"(\w+)\s?(\d{1,2})\s?(?:/|-|de|er|ème|eme)\s?(\d{4})",  # Avril 20 2025
        r"(\d{4})\s?(?:/|-|de|er|ème|eme)\s?(\d{1,2})\s?(?:/|-|de|er|ème|eme)\s?(\d{1,2})",  # 2025/04/20
        r"(Dimanche|Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi)\s?(\d{1,2})\s?(\w+)\s?(\d{4})" #Dimanche 20 avril 2025

    ]
    month_mapping = {
        "janvier": 1, "février": 2, "mars": 3, "avril": 4,
        "mai": 5, "juin": 6, "juillet": 7, "août": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12
    }
    # Time patterns
    time_patterns = [
        r"(\d{1,2})h(\d{2})",  # 10h30
        r"(\d{1,2}):(\d{2})",  # 10:30
        r"(\d{1,2})h",  # 10h
        r"(\d{1,2})[h\s](\d{1,2})-(\d{1,2})[h\s](\d{1,2})", # 10h30-12h30
    ]

    # Find all dates and times
    dates_found = []
    times_found = []

    for pattern in date_patterns:
        dates = re.findall(pattern, text, re.IGNORECASE)
        if dates:
            dates_found.extend(dates)

    for pattern in time_patterns:
        times = re.findall(pattern, text, re.IGNORECASE)
        if times:
            times_found.extend(times)

    # If no dates are found, use the publication date if available
    if not dates_found and date_publication:
        try:
            date_object = datetime.strptime(date_publication, '%Y-%m-%d')
            dates_found = [(date_object.year, date_object.month, date_object.day)]
        except ValueError:
            print(f"Failed to parse publication date: {date_publication}")

    # Process the found dates and times
    for date_info in dates_found:
        year, month, day = None, None, None
        #Determine date format
        if len(date_info) == 3:
            # case like 20/04/2025
            try:
                day = int(date_info[0])
                month = int(date_info[1])
                year = int(date_info[2])
            except:
                pass
        elif len(date_info) == 4:
             # case like Dimanche 20 avril 2025
            try:
                day = int(date_info[1])
                month_name = date_info[2].lower()
                month = month_mapping.get(month_name)
                year = int(date_info[3])
            except:
                pass

        if day is None or month is None or year is None:
            continue # Skip to the next date if parsing failed

        date_object = datetime(year, month, day)
        for time_info in times_found:
            # Determine the time format and extract hours and minutes
            hours, minutes, end_hours, end_minutes = None, None, None, None
            if len(time_info) == 2:
                # Cases like 10h30 or 10:30
                try:
                    hours = int(time_info[0])
                    minutes = int(time_info[1])
                except:
                    pass
            elif len(time_info) == 1:
                # Cases like 10h
                try:
                    hours = int(time_info[0])
                    minutes = 0
                except:
                    pass
            elif len(time_info) == 4:
                try:
                    hours = int(time_info[0])
                    minutes = int(time_info[1])
                    end_hours = int(time_info[2])
                    end_minutes = int(time_info[3])
                except:
                    pass
                
            if hours is None or minutes is None:
                 continue # Skip to the next time if parsing failed

            # Create start and end datetime objects
            start_datetime = datetime(date_object.year, date_object.month, date_object.day, hours, minutes)

            #If end time found
            if end_hours is not None and end_minutes is not None:
                 end_datetime = datetime(date_object.year, date_object.month, date_object.day, end_hours, end_minutes)

                 # Determine AM/PM and format columns for the end time
                 day = end_datetime.strftime('%A').lower()
                 ampm = end_datetime.strftime('%p').lower()
                 start_col = f"{day}_start_hour_{ampm}"
                 end_col = f"{day}_end_hour_{ampm}"

                 results.append({
                     'date': date_object.strftime('%Y-%m-%d'),
                     'start_time': start_datetime.strftime('%H:%M:%S'),
                     'end_time': end_datetime.strftime('%H:%M:%S'),
                     'start_column': start_col,
                     'end_column': end_col
                 })

            # Determine AM/PM and format columns for the start time
            day = start_datetime.strftime('%A').lower()
            ampm = start_datetime.strftime('%p').lower()
            start_col = f"{day}_start_hour_{ampm}"
            end_col = f"{day}_end_hour_{ampm}"

            results.append({
                'date': date_object.strftime('%Y-%m-%d'),
                'start_time': start_datetime.strftime('%H:%M:%S'),
                'end_time': None, # set to None when it is a single time
                'start_column': start_col,
                'end_column': end_col
            })
    return results

# Example Usage with CSV Data
csv_file = 'Supabase-Snippet-Event-Management-Table.csv'
df = pd.read_csv(csv_file)

# Assuming the text is in the second column (index 1) and publication date in column with header "date_publication"
df['extracted_info'] = df.apply(lambda row: extract_date_and_time(row.iloc[1], row['date_publication']), axis=1)

# Print the DataFrame with the extracted information
print(df[['id', 'extracted_info']]) # showing only 'id' and 'extracted_info' columns
