

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
# shapefile_path = r'C:\Users\AbhilasaBarman\Downloads\SSP245&585_shp\SSP245_ClimateData_India.shp'
shapefile_path = r'C:\Users\AbhilasaBarman\OneDrive - Azim Premji Foundation\Documents\SSP245&585_shp'
gdf = gpd.read_file(shapefile_path)

# Ensure all relevant columns are numeric
numeric_columns = ['Population', 'HWDI_per_r', 'HWDI_per_t', 'Annual_RF_', 'JJAS_RF_Ch', 'OND_RF_Cha', 
                   'TMAX_Annua', 'TMAX_MAM_C', 'TMIN_Annua', 'TMIN_DJF_C', 'JJAS_CDD_P', 'OND_CDD_Pe', 
                   'MAM_CSU_pe', 'MAM_CSU__1', 'WSDI_wrt_9', 'Warm_spell', 'JJAS_R10MM', 'OND_R10MM_', 
                   'JJAS_R20MM', 'OND_R20MM_', 'RX1Day_JJA', 'RX1Day_OND', 'RX5day_JJA', 'F5day_even', 
                   'RX5day_OND', 'F5day_ev_1', 'SDII_JJAS', 'SDII_OND', 'Rainy_Days', 'Rainy_Da_1', 
                   'Summer_Day', 'Annual_Wet', 'MAM_Wet_Bu']

for col in numeric_columns:
    gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)

# Transform coordinates to Web Mercator
gdf = transform_to_web_mercator(gdf)

# Convert the GeoDataFrame to GeoJSON format
gdf_json = json.loads(gdf.to_json())

# Create a GeoJSONDataSource from the GeoJSON data
geo_source = GeoJSONDataSource(geojson=json.dumps(gdf_json))

# Define the output file
output_file("ssp245_map.html", title="Climate Data Map (SSP245)")

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
p.add_tile("CartoDB Positron")
# xyz_provider =  xyzservices.TileProvider(name="Google Maps",
#                                              url=" https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
#                                              attribution="(C) xyzservices",
#                                              )  

# p.add_tile(xyz_provider,alpha=0.5)


# Set initial map bounds to prevent resizing on selection
p.x_range = Range1d(start=gdf.total_bounds[0], end=gdf.total_bounds[2])
p.y_range = Range1d(start=gdf.total_bounds[1], end=gdf.total_bounds[3])

# Define color mappers for each parameter
parameter_palettes = {
    'Population': Turbo256,
    'HWDI_per_r': Viridis256,
    'HWDI_per_t': Inferno256,
    'Annual_RF_': Cividis256,
    'JJAS_RF_Ch': Plasma256,
    'OND_RF_Cha': Turbo256,
    'TMAX_Annua': Viridis256,
    'TMAX_MAM_C': Inferno256,
    'TMIN_Annua': Cividis256,
    'TMIN_DJF_C': Plasma256,
    'JJAS_CDD_P': Turbo256,
    'OND_CDD_Pe': Viridis256,
    'MAM_CSU_pe': Inferno256,
    'MAM_CSU__1': Cividis256,
    'WSDI_wrt_9': Plasma256,
    'Warm_spell': Turbo256,
    'JJAS_R10MM': Viridis256,
    'OND_R10MM_': Inferno256,
    'JJAS_R20MM': Cividis256,
    'OND_R20MM_': Plasma256,
    'RX1Day_JJA': Turbo256,
    'RX1Day_OND': Viridis256,
    'RX5day_JJA': Inferno256,
    'F5day_even': Cividis256,
    'RX5day_OND': Plasma256,
    'F5day_ev_1': Turbo256,
    'SDII_JJAS': Viridis256,
    'SDII_OND': Inferno256,
    'Rainy_Days': Cividis256,
    'Rainy_Da_1': Plasma256,
    'Summer_Day': Turbo256,
    'Annual_Wet': Viridis256,
    'MAM_Wet_Bu': Inferno256
}

# Define parameter descriptions
parameter_descriptions = {
    'Population': 'Total population in the area(2011).',
    'HWDI_per_r': 'Heatwave Duration Index per region.',
    'HWDI_per_t': 'Heatwave Duration Index per time period.',
    'Annual_RF_': 'Annual rainfall.',
    'JJAS_RF_Ch': 'Rainfall changes in Southwest monsoon (JJAS).',
    'OND_RF_Cha': 'Rainfall changes in Northeast monsoon (OND).',
    'TMAX_Annua': 'Maximum temperature annually.',
    'TMAX_MAM_C': 'Maximum temperature in Summer (MAM).',
    'TMIN_Annua': 'Minimum temperature annually.',
    'TMIN_DJF_C': 'Minimum temperature in Winter (DJF).',
    'JJAS_CDD_P': 'Consecutive dry days in Southwest monsoon (JJAS).',
    'OND_CDD_Pe': 'Consecutive dry days in Northeast monsoon (OND).',
    'MAM_CSU_pe': 'Cold spell duration in Summer (MAM).',
    'MAM_CSU__1': 'Cold spell duration in Summer (MAM) (alternative measure).',
    'WSDI_wrt_9': 'Warm spell duration index with respect to 90th percentile.',
    'Warm_spell': 'Warm spell duration.',
    'JJAS_R10MM': 'Number of days with more than 10mm rain in Southwest monsoon (JJAS).',
    'OND_R10MM_': 'Number of days with more than 10mm rain in Northeast monsoon (OND).',
    'JJAS_R20MM': 'Number of days with more than 20mm rain in Southwest monsoon (JJAS).',
    'OND_R20MM_': 'Number of days with more than 20mm rain in Northeast monsoon (OND).',
    'RX1Day_JJA': 'Maximum one-day rainfall in Southwest monsoon (JJAS).',
    'RX1Day_OND': 'Maximum one-day rainfall in Northeast monsoon (OND).',
    'RX5day_JJA': 'Maximum five-day rainfall in Southwest monsoon (JJAS).',
    'F5day_even': 'Maximum five-day rainfall events.',
    'RX5day_OND': 'Maximum five-day rainfall in Northeast monsoon (OND).',
    'F5day_ev_1': 'Maximum five-day rainfall events (alternative measure).',
    'SDII_JJAS': 'Simple daily intensity index in Southwest monsoon (JJAS).',
    'SDII_OND': 'Simple daily intensity index in Northeast monsoon (OND).',
    'Rainy_Days': 'Total number of rainy days.',
    'Rainy_Da_1': 'Total number of rainy days (alternative measure).',
    'Summer_Day': 'Total number of summer days.',
    'Annual_Wet': 'Annual wet days.',
    'MAM_Wet_Bu': 'Wet days in Summer (MAM).'
}


# Define initial color mapper for population
initial_param = 'Population'
color_mapper = LinearColorMapper(palette=parameter_palettes[initial_param], low=gdf[initial_param].min(), high=gdf[initial_param].max())

# Add patches (polygons) to the figure
patches = p.patches(
    'xs', 'ys',
    source=geo_source,
    fill_color={'field': initial_param, 'transform': color_mapper},
    line_color="black",
    line_width=0.5,
    fill_alpha=0.7,
    name="patches"
)

# Add hover tool
hover = HoverTool()
hover.tooltips = [("State", "@State"), ("District", "@District"), (initial_param, f"@{initial_param}")]
p.add_tools(hover)

# Create a color bar for the population
color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=BasicTicker(desired_num_ticks=10),
    formatter=PrintfTickFormatter(format="%.2f"),
    label_standoff=12,
    border_line_color=None,
    location=(0, 0)
)

p.add_layout(color_bar, 'left')



# Create a Select widget for parameters
parameters = numeric_columns
parameter_select = Select(title="Select Parameter:", value=parameters[0], options=parameters,styles={'background-color': '#4682B4', 'color': 'white','font-family': 'Arial, sans-serif', 'font-size': '14px'})



# Create a Div widget for parameter descriptions
# description_div = Div(text=f"<b style='font-size:16px;'>{parameter_descriptions[initial_param]}</b>", width=800, height=50)
# Create a Div widget for parameter descriptions with initial parameter and its description
description_div = Div(text=f"<b style='font-size:16px;'>{initial_param}: {parameter_descriptions[initial_param]}</b>", width=800, height=50)


# Create initial boxplot data
def create_boxplot_data(parameter, values):
    if values.empty:
        return dict(q1=[0], q2=[0], q3=[0], upper=[0], lower=[0])
    q1 = values.quantile(0.25)
    q2 = values.quantile(0.50)
    q3 = values.quantile(0.75)
    iqr = q3 - q1
    upper = min(q3 + 1.5 * iqr, values.max())
    lower = max(q1 - 1.5 * iqr, values.min())
    return dict(q1=[q1], q2=[q2], q3=[q3], upper=[upper], lower=[lower])

# Empty initial boxplot data
# initial_boxplot_data = create_boxplot_data(parameters[0], pd.Series([]))
# boxplot_source = ColumnDataSource(data=initial_boxplot_data)
initial_boxplot_data = dict(q1=[], q2=[], q3=[], upper=[], lower=[])
boxplot_source = ColumnDataSource(data=initial_boxplot_data)

# Create the initial boxplot
p_box = figure(title="Boxplot", width=600, height=400)
p_box.segment(0, 'upper', 0, 'q3', source=boxplot_source, line_color="black")
p_box.segment(0, 'lower', 0, 'q1', source=boxplot_source, line_color="black")
p_box.vbar(x=0, width=0.7, bottom='q2', top='q3', source=boxplot_source, fill_color="#598090", line_color="black")
p_box.vbar(x=0, width=0.7, bottom='q1', top='q2', source=boxplot_source, fill_color="#bb7b85", line_color="black")
p_box.rect(0, 'upper', 0.2, 0.01, source=boxplot_source, line_color="black")
p_box.rect(0, 'lower', 0.2, 0.01, source=boxplot_source, line_color="black")
p_box.xgrid.grid_line_color = None
p_box.y_range.start = 0
p_box.y_range.start = min(gdf[initial_param].min(), -20)
# p_box.y_range.end = max(gdf[initial_param].max(),99999)
p_box.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically

# Create a ColumnDataSource for the bar plot
bar_source = ColumnDataSource(data=dict(districts=[], values=[], colors=[]))

# Create the bar plot
p_bar = figure(x_range=[], title="Bar Plot", width=800, height=400)
p_bar.vbar(x='districts', top='values', width=0.9, color='colors', source=bar_source)
p_bar.xgrid.grid_line_color = None
# p_bar.y_range.start = 0
p_bar.y_range.start = min(gdf[initial_param].min(), -20) 
p_bar.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically


state_district_map = {state: gdf[gdf['State'] == state]['District'].unique().tolist() for state in gdf['State'].unique()}
# Create Select widgets
state_select = Select(title="Select State:", options=sorted(gdf['State'].unique().tolist()),styles={'background-color': '#4682B4', 'color': 'white','font-family': 'Arial, sans-serif', 'font-size': '14px'})
district_select = Select(title="Select District:", options=[],styles={'background-color': '#4682B4', 'color': 'white','font-family': 'Arial, sans-serif', 'font-size': '14px'})
# district_select = Select(title="Select District:", options=sorted(gdf['District'].unique().tolist()))

# Add a callback to highlight the selected state
state_select_callback = CustomJS(
    args=dict(source=geo_source, state_select=state_select,district_select=district_select,state_district_map=state_district_map,boxplot_source=boxplot_source, bar_source=bar_source, parameter_select=parameter_select, p_box=p_box, p_bar=p_bar,patches=patches),
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
    patches.glyph.visible = True
    console.log(source.selected.indices)

    //Update district dropdown options
    district_select.options = state_district_map[state];
    district_select.value = '';

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
    # Set the y-axis range with an additional padding and ensure min is at least -20
    p_bar.y_range.start = Math.min(0, ...district_values);
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

    // Update description text
    description_div.text = `<b style='font-size:16px;'>${selected_param}: ${parameter_descriptions[selected_param]}</b>`;


    // Update color mapper and patches
    color_mapper.palette = parameter_palettes[selected_param];
    color_mapper.low = Math.min(...gdf.features.map(f => f.properties[selected_param]));
    color_mapper.high = Math.max(...gdf.features.map(f => f.properties[selected_param]));
    patches.glyph.fill_color = { field: selected_param, transform: color_mapper };

    // Update hover tool
    hover.tooltips = [["State", "@State"], ["District", "@District"], [selected_param, `@${selected_param}`]];

    const selected = geo_source.selected.indices;

    if (selected.length > 0) {
        const state = geo_source.data['State'][selected[0]];

        // Filter values based on the selected state
        const values = geo_source.data[selected_param].filter((value, index) => geo_source.data['State'][index] === state);
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
                if (geo_source.data['District'][i] === selected_district) {
                    colors.push('#dc6601');
                } else {
                    colors.push('#006ca5');
                }
            }
        }

        bar_source.data = { districts: districts, values: district_values, colors: colors };
        p_bar.x_range.factors = districts;
        p_bar.title.text = `${selected_param} in ${state}`;
        p_bar.y_range.start = Math.min(0, ...district_values);
        console.log("p_bar.y_range.start", p_bar.y_range.start);

    } else {
        // Update boxplot data for the entire state
        const values = gdf.features.map(f => f.properties[selected_param]);
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
        p_box.title.text = `${selected_param}`;
    }
"""
);

parameter_select.js_on_change('value', callback)



tap_callback = CustomJS(
    args=dict(source=geo_source, boxplot_source=boxplot_source, bar_source=bar_source, parameter_select=parameter_select, p_box=p_box, p_bar=p_bar, patches=patches),
    code="""
    console.log("tapcallback")

    console.log(source.selected.indices)
    source.selected.indices = [source.selected.indices.pop()];  
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
        p_bar.y_range.start = Math.min(0, ...district_values)
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

# Create a Select widget for sorting options
sort_select = Select(title="Sort Order:", value=" ", options=["Ascending", "Descending"])

# Callback to update the bar plot based on the selected sort order
sort_callback = CustomJS(args=dict(bar_source=bar_source, p_bar=p_bar), code="""
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

layout = column(row(parameter_select,description_div,state_select, district_select),row(p,sort_select,column(p_bar,p_box)))

show(layout)








