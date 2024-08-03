

import os
import xyzservices
import geopandas as gpd
import pandas as pd
import json
import shapely
from bokeh.io import output_file, show
from bokeh.models import BasicTicker, PrintfTickFormatter, TapTool, CustomJS, Legend, LegendItem,Select,Div
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, HoverTool, Select, ColumnDataSource, Range1d, ColorBar, LinearColorMapper
from bokeh.layouts import column, row
from bokeh.palettes import Turbo256, Viridis256, Inferno256, Cividis256, Plasma256
from bokeh.io import show
from bokeh.models import Range1d
from bokeh.layouts import layout


from pyproj import Transformer

# Function to transform lat/lon to Web Mercator
def transform_to_web_mercator(gdf):
    transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
    gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.ops.transform(transformer.transform, geom))
    return gdf

# Load your shapefile using Geopandas
shapefile_path = r'C:\Users\AbhilasaBarman\OneDrive - Azim Premji Foundation\Documents\climate_data_app\SSP245&585_shp\SSP585_ClimateData_India.shp'
# shapefile_path = r'C:\Users\AbhilasaBarman\OneDrive - Azim Premji Foundation\Documents\SSP245&585_shp'


gdf_old = gpd.read_file(shapefile_path)

# Parameters to include and their new names
include_parameters = ['Annual_RF_', 'TMAX_Annua','TMAX_MAM_C','TMIN_DJF_C','HWDI_per_t',
                      'JJAS_RF_Ch','OND_RF_Cha','JJAS_CDD_1','OND_CDD__1','JJAS_R20_1',
                      'OND_R20MM1','RX5day_JJA','Annual_Wet','MAM_Wet_Bu','Annual_RH_','MAM_RH_Cha']
rename_mapping = {
    'TMAX_Annua': "Annual change in maximum temperature (C)",
    'TMAX_MAM_C': "Change in maximum temperature during summer (C)",
    'TMIN_DJF_C': "Change in minimum temperature during winter (C)",
    'HWDI_per_t': "Heat wave index",
    'Annual_RF_': "Change in annual Rainfall",
    'JJAS_RF_Ch': "Change in Precipitation during monsoon",
    'OND_RF_Cha': "Change in Precipitation during retreating monsoon",
    'JJAS_CDD_1': "Change in continuous dry days during monsoon",
    'OND_CDD__1': "Change in continuous dry days during retreating monsoon",
    'JJAS_R20_1': "Change in number of days with precipitation greater than 20mm during monsoon",
    'OND_R20MM1': "Change in number of days with precipitation greater than 20mm during retreating monsoon",
    'RX5day_JJA': "Change in highest five-day precipitation during monsoon",
    'Annual_Wet': "Annual wet bulb temperature (C)",
    'MAM_Wet_Bu': "Summer wet bulb temperature (C)",
    'Annual_RH_': "Annual change in relative humidity",
    'MAM_RH_Cha': "Change in relative humidity during summer"

}

# Keep only the columns specified in include_parameters
gdf_temp = gdf_old[include_parameters + ['State','District','geometry']]



gdf = gdf_temp.rename(columns=rename_mapping)

numeric_columns = [
    'Annual change in maximum temperature (C)',
    'Change in maximum temperature during summer (C)',
    'Change in minimum temperature during winter (C)',
    'Heat wave index',
    'Change in annual Rainfall',
    'Change in Precipitation during monsoon',
    'Change in Precipitation during retreating monsoon',
    'Change in continuous dry days during monsoon',
    'Change in continuous dry days during retreating monsoon',
    'Change in number of days with precipitation greater than 20mm during monsoon',
    'Change in number of days with precipitation greater than 20mm during retreating monsoon',
    'Change in highest five-day precipitation during monsoon',
    'Annual wet bulb temperature (C)',
    'Summer wet bulb temperature (C)',
    'Annual change in relative humidity',
    'Change in relative humidity during summer'
]


for col in numeric_columns:
    gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)

# Transform coordinates to Web Mercator
gdf = transform_to_web_mercator(gdf)

# Convert the GeoDataFrame to GeoJSON format
gdf_json = json.loads(gdf.to_json())

# Create a GeoJSONDataSource from the GeoJSON data
geo_source = GeoJSONDataSource(geojson=json.dumps(gdf_json))
# print(geo_source.geojson[:1000]) 


# Define the output file
output_file("ssp585_map.html", title="Climate Data Map (SSP585)")

# Create the figure
p = figure(
    title="Climate Map",
    x_axis_type="mercator",
    y_axis_type="mercator",
    # tools="pan,wheel_zoom,zoom_in,zoom_out,reset,tap",
    tools="pan,wheel_zoom,zoom_in,zoom_out,reset",
    width=900,
    height=800
)

# Add tile provider (map background)
# p.add_tile("CartoDB Positron")
xyz_provider =  xyzservices.TileProvider(name="Google Maps",
                                             url=" https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                                             attribution="(C) xyzservices",
                                             )  

p.add_tile(xyz_provider,alpha=0.5)


# Set initial map bounds to prevent resizing on selection
p.x_range = Range1d(start=gdf.total_bounds[0], end=gdf.total_bounds[2])
p.y_range = Range1d(start=gdf.total_bounds[1], end=gdf.total_bounds[3])

# Define color mappers for each parameter
parameter_palettes = {

    'Annual change in maximum temperature (C)': Viridis256,
    'Change in maximum temperature during summer (C)': Inferno256,
    'Change in minimum temperature during winter (C)': Plasma256,
    'Heat wave index': Inferno256,
    'Change in annual Rainfall': Cividis256,
    'Change in Precipitation during monsoon' : Plasma256,
    'Change in Precipitation during retreating monsoon' : Turbo256,
    'Change in continuous dry days during monsoon' : Turbo256,
    'Change in continuous dry days during retreating monsoon' : Viridis256,
    'Change in number of days with precipitation greater than 20mm during monsoon' : Cividis256,
    'Change in number of days with precipitation greater than 20mm during retreating monsoon' : Plasma256,
    'Change in highest five-day precipitation during monsoon' : Inferno256,
    'Annual wet bulb temperature (C)' : Viridis256,
    'Summer wet bulb temperature (C)' : Inferno256,
    'Annual change in relative humidity' : Cividis256,
    'Change in relative humidity during summer' : Turbo256
}

# Define parameter descriptions
parameter_descriptions = {
    'Annual change in maximum temperature (C)': "Yearly variation in the highest temperature recorded.",
    'Change in maximum temperature during summer (C)': " Variation in summer's highest temperatures over time.",
    'Change in minimum temperature during winter (C)': "Variation in the lowest winter temperatures.",
    'Heat wave index': "Measures the frequency and intensity of heat waves.",
    'Change in annual Rainfall': "Yearly variation in total precipitation.",
    'Change in Precipitation during monsoon' : "Variation in monsoon rainfall amounts.",
    'Change in Precipitation during retreating monsoon' : "Variation in rainfall during the monsoon's retreat phase.",
    'Change in continuous dry days during monsoon' : "Variation in consecutive dry days during the monsoon season.",
    'Change in continuous dry days during retreating monsoon' : "Variation in consecutive dry days during the retreating monsoon.",
    'Change in number of days with precipitation greater than 20mm during monsoon' : "Variation in the number of days with heavy rainfall during the monsoon.",
    'Change in number of days with precipitation greater than 20mm during retreating monsoon' : " Variation in the number of days with heavy rainfall during the retreating monsoon.",
    'Change in highest five-day precipitation during monsoon' : "Variation in maximum five-day precipitation totals during the monsoon.",
    'Annual wet bulb temperature (C)' : " Average annual temperature considering humidity.",
    'Summer wet bulb temperature (C)' : "Average summer temperature including humidity.",
    'Annual change in relative humidity' : 'Yearly variation in relative humidity.',
    'Change in relative humidity during summer' : 'Variation in relative humidity specifically during the summer months.' 
 }


# Define initial color mapper for population
# initial_param = 'Population' 
initial_param = 'Change in annual Rainfall'
color_mapper = LinearColorMapper(palette=parameter_palettes[initial_param], low=gdf[initial_param].min(), high=gdf[initial_param].max())
initial_fill_color = "#FFFF9E" 
# Add patches (polygons) to the figure
patches = p.patches(
    'xs', 'ys',
    source=geo_source,
    # fill_color={'field': initial_param, 'transform': color_mapper},
    fill_color=initial_fill_color,
    line_color="black",
    line_width=0.5,
    fill_alpha=0.5,
    name="patches"
)

# Add hover tool
# hover = HoverTool()
# hover.tooltips = [("State", "@State"), ("District", "@District"), (initial_param, f"@{initial_param}")]
# p.add_tools(hover)
hover = HoverTool()
hover.tooltips = [("State", "@State"), ("District", "@District")]
p.add_tools(hover)

# Create a color bar for the population
color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=BasicTicker(desired_num_ticks=10),
    formatter=PrintfTickFormatter(format="%.2f"),
    label_standoff=12,
    border_line_color=None,
    location=(0, 0),
    visible= False
)

p.add_layout(color_bar, 'left')



# Create a Select widget for parameters
parameters = numeric_columns
parameter_select = Select(title="Select Parameter:", value=[], options=parameters,styles={'background-color': '#4682B4', 'color': 'white','font-family': 'Arial, sans-serif', 'font-size': '14px'})


# Create a Div widget for parameter descriptions with initial parameter and its description
description_div = Div(text=f"<b style='font-size:16px;'>{initial_param}: {parameter_descriptions[initial_param]}</b>", width=1000, height=50, visible = False)
description_div_head = Div(
    text=f"<h2>Description of the Parameter Selected</h2>",
    width=1000,
    height=50  # Adjust the height if needed to fit both lines
)


# Empty initial boxplot data
initial_boxplot_data = dict(q1=[], q2=[], q3=[], upper=[], lower=[])
boxplot_source = ColumnDataSource(data=initial_boxplot_data)

# Create the initial boxplot
p_box = figure(title="Boxplot", width=600, height=400)
p_box.segment(0, 'upper', 0, 'q3', source=boxplot_source, line_color="black")
p_box.segment(0, 'lower', 0, 'q1', source=boxplot_source, line_color="black")
p_box.vbar(x=0, width=0., bottom='q2', top='q3', source=boxplot_source, fill_color="#598090", line_color="black")
p_box.vbar(x=0, width=0.7, bottom='q1', top='q2', source=boxplot_source, fill_color="#bb7b85", line_color="black")
p_box.rect(0, 'upper', 0.2, 0.01, source=boxplot_source, line_color="black")
p_box.rect(0, 'lower', 0.2, 0.01, source=boxplot_source, line_color="black")
p_box.xgrid.grid_line_color = None
p_box.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically


# Create a ColumnDataSource for the bar plot
bar_source = ColumnDataSource(data=dict(districts=[], values=[], colors=[]))
# Create the bar plot
p_bar = figure(x_range=[], title="Bar Plot", width=800, height=400)
p_bar.vbar(x='districts', top='values', width=0.9, color='colors', source=bar_source)
p_bar.xgrid.grid_line_color = None
p_bar.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically

# configure the tooltip 
hover_two = HoverTool(tooltips=[("Value", "@values")]) 
p_bar.add_tools(hover_two)

state_district_map = {state: gdf[gdf['State'] == state]['District'].unique().tolist() for state in gdf['State'].unique()}
# Create Select widgets
state_select = Select(title="Select State:", options=sorted(gdf['State'].unique().tolist()),styles={'background-color': '#4682B4', 'color': 'white','font-family': 'Arial, sans-serif', 'font-size': '14px'})
district_select = Select(title="Select District:", options=[],styles={'background-color': '#4682B4', 'color': 'white','font-family': 'Arial, sans-serif', 'font-size': '14px'})
# district_select = Select(title="Select District:", options=sorted(gdf['District'].unique().tolist()))

# Create a Select widget for sorting options
sort_select = Select(title="Sort Order:", value=" ", options=["Ascending", "Descending"])


# Add a callback to highlight the selected state
state_select_callback = CustomJS(
    args=dict(source=geo_source, state_select=state_select,district_select=district_select,state_district_map=state_district_map,boxplot_source=boxplot_source, bar_source=bar_source, parameter_select=parameter_select, p_box=p_box, p_bar=p_bar,patches=patches,sort_select=sort_select),
    code="""

    console.log("state callback")

    // Highlight the selected state
    var data = source.data;
    var state = state_select.value; 
    const selected_param = parameter_select.value;  

    var selected_indices = [];
    for (var i = 0; i < data['State'].length; i++) {
        if (data['State'][i] == state) {
            selected_indices.push(i);
        }
    }
    source.selected.indices = selected_indices;
 
    source.change.emit();
    console.log(source.selected.indices)

    //Update district dropdown options
    district_select.options = state_district_map[state];
    //district_select.value = '';

    // Filter values based on the selected state
    const values = source.data[selected_param].filter((value, index) => source.data['State'][index] === state);
    values.sort((a, b) => a - b);
    const q1 = values[Math.floor((values.length / 4))];
    const q2 = values[Math.floor((values.length / 2))];
    const q3 = values[Math.floor((3 * values.length) / 4)];
    const iqr = q3 - q1;
    const upper = Math.min(q3 + 1.5 * iqr, Math.max(...values));
    const lower = Math.max(q1 - 1.5 * iqr, Math.min(...values));
    const boxplot_data = {
        q1: [q1],
        q2: [q2],
        q3: [q3],
        upper: [upper],
        lower: [lower]
    };
    boxplot_source.data = boxplot_data;
        p_box.y_range.start = lower
        p_box.y_range.end = upper
        p_box.y_range.change.emit();

    p_box.title.text = `${selected_param} in ${state}`;

    // Update bar plot data for selected parameter for all districts in the state
    const districts = [];
    const district_values = [];
    const colors = [];
    for (let i = 0; i < source.data['State'].length; i++) {
        if (source.data['State'][i] === state) {
            districts.push(source.data['District'][i]);
            district_values.push(source.data[selected_param][i]);
            colors.push('#006ca5');
        }
    }
    console.log(districts)

    bar_source.data = { districts: districts, values: district_values, colors: colors };
    p_bar.x_range.factors = districts;
    p_bar.title.text = `${selected_param} in ${state}`;

    // Calculate the minimum and maximum of the district values
    const min_value = Math.min(...district_values);
    const max_value = Math.max(...district_values);

    // Set the y-axis range to span from the minimum to the maximum value
    p_bar.y_range.start = min_value;
    p_bar.y_range.end = max_value;
    console.log(p_bar.y_range)
    """
)

state_select.js_on_change('value', state_select_callback)


# Callback for district select dropdown
district_select_callback = CustomJS(
    args=dict(source=geo_source, district_select=district_select, parameter_select=parameter_select, bar_source=bar_source, p_bar=p_bar),
    code="""
    const selected_district = district_select.value;
    const selected_param = parameter_select.value;
    var data = source.data;
    // Filter values based on the selected district
    const districts = source.data['District'];
    const param_values = source.data[selected_param];
    const selected_index = districts.indexOf(selected_district);
    const selected_value = param_values[selected_index];

    console.log("district callback")
    console.log("districts",districts)
    console.log("selected_value",selected_value)

    var selected_indices = [];
    for (var i = 0; i < districts.length; i++) {
        if (districts[i] === selected_district) {
            selected_indices.push(i);
        }
    }

    console.log("selected_indices", selected_indices);

    source.selected.indices = selected_indices;
    source.change.emit();


    // Update bar plot data
    bar_source.data ={
        districts: [selected_district],
        values: [selected_value],
        colors: ['#dc6601']  // Highlight color for selected district
    };
    p_bar.x_range.factors = [selected_district];
    p_bar.title.text = `${selected_param} in ${selected_district}`;
    p_bar.y_range.start = Math.min(0, selected_value);  // Adjust y-axis range if necessary

    """
)

district_select.js_on_change('value', district_select_callback)


callback = CustomJS(
    args=dict(geo_source=geo_source, color_mapper=color_mapper, patches=patches, color_bar=color_bar,
              hover=hover, parameter_select=parameter_select, description_div=description_div, parameter_descriptions=parameter_descriptions,
              gdf=gdf_json, parameter_palettes=parameter_palettes, boxplot_source=boxplot_source, p_box=p_box, p_bar=p_bar, bar_source=bar_source),
    code="""

    console.log("callback")
    const selected_param = parameter_select.value;
    console.log("selected_param",selected_param)
    // Update description text
    description_div.text = `<b style='font-size:16px;'>${selected_param}: ${parameter_descriptions[selected_param]}</b>`;
    description_div.visible = true;

    // Update color mapper and patches
   
    color_mapper.palette = parameter_palettes[selected_param];
    color_mapper.low = Math.min(...gdf.features.map(f => f.properties[selected_param]));
    color_mapper.high = Math.max(...gdf.features.map(f => f.properties[selected_param]));
    patches.glyph.fill_color = { field: selected_param, transform: color_mapper };
    color_bar.color_mapper = color_mapper
    color_bar.visible = true
 
    // Update hover tool
    //hover.tooltips = [["State", "@State"], ["District", "@District"], [selected_param, '@${selected_param}']];
    //console.log("hover tooltips:", hover.tooltips);
    // Update hover tool to include selected parameter
    //hover.tooltips = [
    //    ["State", "@State"],
    //    ["District", "@District"],
    //    [selected_param,`@${selected_param}`]
    //];
    //hover.tooltips.append([selected_param, f"@{selected_param}"])

    //hover.change.emit();

    const selected = geo_source.selected.indices;

    console.log("selected",selected)

    if (selected.length > 0) {
        const state = geo_source.data['State'][selected[0]];
        console.log("inside the if statement")
        // Filter values based on the selected state
        const values = geo_source.data[selected_param].filter((value, index) => geo_source.data['State'][index] === state);
        values.sort((a, b) => a - b);
        const q1 = values[Math.floor((values.length / 4))];
        const q2 = values[Math.floor((values.length / 2))];
        const q3 = values[Math.floor((3 * values.length) / 4)];
        const iqr = q3 - q1;
        const upper = Math.min(q3 + 1.5 * iqr, Math.max(...values));
        const lower = Math.max(q1 - 1.5 * iqr, Math.min(...values));
        console.log("upper,lower",upper," ",lower)
        const boxplot_data = {
            q1: [q1],
            q2: [q2],
            q3: [q3],
            upper: [upper],
            lower: [lower]
        };
        boxplot_source.data = boxplot_data;
        p_box.y_range.start = lower
        p_box.y_range.end = upper
        p_box.y_range.change.emit();        
        p_box.title.text = `${selected_param} in ${state}`;

        // Update bar plot data for selected parameter for all districts in the state
        const districts = [];
        const district_values = [];
        const colors = [];
        const selected_district = geo_source.data['District'][selected[0]];
        for (let i = 0; i < geo_source.data['State'].length; i++) {
            if (geo_source.data['State'][i] === state) {
                districts.push(geo_source.data['District'][i]);
                district_values.push(geo_source.data[selected_param][i]);
                colors.push('#006ca5')
                //if (geo_source.data['District'][i] === selected_district) {
                //    colors.push('#dc6601');
                //} else {
                //    colors.push('#006ca5');
                //}
            }
        }

        bar_source.data = { districts: districts, values: district_values, colors: colors };
        p_bar.x_range.factors = districts;
        p_bar.title.text = `${selected_param} in ${state}`;
        // Calculate the minimum and maximum of the district values
        const min_value = Math.min(...district_values);
        const max_value = Math.max(...district_values);

        // Set the y-axis range to span from the minimum to the maximum value
        p_bar.y_range.start = min_value;
        p_bar.y_range.end = max_value;

    } else {
        // Update boxplot data for the entire india

        const values = gdf.features.map(f => f.properties[selected_param]);

        console.log("values",values)

        values.sort((a, b) => a - b);
        const q1 = values[Math.floor((values.length / 4))];
        const q2 = values[Math.floor((values.length / 2))];
        const q3 = values[Math.floor((3 * values.length) / 4)];
        const iqr = q3 - q1;
        const upper = Math.min(q3 + 1.5 * iqr, Math.max(...values));
        const lower = Math.max(q1 - 1.5 * iqr, Math.min(...values));

        console.log("upper",upper)
        console.log("lower",lower)

        const boxplot_data = {
            q1: [q1],
            q2: [q2],
            q3: [q3],
            upper: [upper],
            lower: [lower]
        };
        boxplot_source.data = boxplot_data;
        p_box.y_range.start = lower
        p_box.y_range.end = upper
        p_box.y_range.change.emit();
        p_box.title.text = `${selected_param}`;
    }
"""
);

parameter_select.js_on_change('value', callback)



tap_callback = CustomJS(
    args=dict(source=geo_source, boxplot_source=boxplot_source, bar_source=bar_source, parameter_select=parameter_select, p_box=p_box,
               p_bar=p_bar, patches=patches,district_select=district_select,state_select=state_select),
    code="""

    console.log("tapcallback working")
    //state_select.value = []
    //district_select.value = []
    
    source.selected.indices = [source.selected.indices.pop()]; 
    source.change.emit();
    console.log("source.selected.indices",source.selected.indices)

    const selected_param = parameter_select.value
    if(source.selected.indices.length > 0) {
    const state = source.data['State'][source.selected.indices]

    //Update boxplot for selected parameter and state
    const values = source.data[selected_param].filter((value, index) => source.data['State'][index] === state);
        values.sort((a, b) => a - b);
        const q1 = values[Math.floor((values.length / 4))];
        const q2 = values[Math.floor((values.length / 2))];
        const q3 = values[Math.floor((3 * values.length) / 4)];
        const iqr = q3 - q1;
        const upper = Math.min(q3 + 1.5 * iqr, Math.max(...values));
        const lower = Math.max(q1 - 1.5 * iqr, Math.min(...values));
        console.log("upper",upper)
        console.log("lower",lower)
        const boxplot_data = {
            q1: [q1],
            q2: [q2],
            q3: [q3],
            upper: [upper],
            lower: [lower]
        };
        boxplot_source.data = boxplot_data;
        p_box.y_range.start = lower
        p_box.y_range.end = upper
        p_box.y_range.change.emit();        
        p_box.title.text = `${selected_param} in ${state}`;

        // Update bar plot data for selected parameter for all districts in the state
        const districts = [];
        const district_values = [];
        const colors = [];
        const selected_district = source.data['District'][source.selected.indices];
        for (let i = 0; i < source.data['State'].length; i++) {
            if (source.data['State'][i] === state) {
                districts.push(source.data['District'][i]);
                district_values.push(source.data[selected_param][i]);
                console.log("district_values",district_values)
                if (source.data['District'][i] === selected_district) {
                    colors.push('#dc6601');
                } else {
                    colors.push('#006ca5');
                }
               
            }
            }
        bar_source.data = {districts: districts, values: district_values, colors: colors};
        p_bar.x_range.factors = districts;
        p_bar.title.text = `${selected_param} in ${state}`;

        const min_value = Math.min(...district_values);
        const max_value = Math.max(...district_values);

        // Set the y-axis range to span from the minimum to the maximum value
        p_bar.y_range.start = min_value;
        p_bar.y_range.end = max_value;
    }    
"""
)


# p.js_on_event('tap', tap_callback)
tap = TapTool()
tap.callback = tap_callback
p.add_tools(tap)  


# Function to update bar plot data based on sorting
def update_bar_plot(sort_order):
    sorted_data = sorted(zip(bar_source.data['districts'], bar_source.data['values']), key=lambda x: x[1], reverse=(sort_order == "Descending"))
    districts, values = zip(*sorted_data)
    bar_source.data = dict(districts=districts, values=values, colors=['#006ca5'] * len(districts))
    p_bar.x_range.factors = list(districts)


# Callback to update the bar plot based on the selected sort order
sort_callback = CustomJS(args=dict(bar_source=bar_source, p_bar=p_bar), code="""
    console.log("sort function working")                     
    const sort_order = this.value;
    const districts = bar_source.data['districts'];
    const values = bar_source.data['values'];
    let data = [];
    for (let i = 0; i < districts.length; i++) {
        data.push({district: districts[i], value: values[i]});
    }
    data.sort((a, b) => sort_order === "Descending" ? b.value - a.value : a.value - b.value);
    bar_source.data['districts'] = data.map(d => d.district);
    bar_source.data['values'] = data.map(d => d.value);
    bar_source.change.emit();
    p_bar.x_range.factors = data.map(d => d.district);
""")

sort_select.js_on_change('value', sort_callback)

# layout = column(description_div_head,row(description_div,state_select,parameter_select),row(p,sort_select,column(p_bar,p_box)))
layout = column(row(description_div_head,state_select,district_select,parameter_select),description_div,row(p,sort_select,column(p_bar,p_box)))
show(layout)

































