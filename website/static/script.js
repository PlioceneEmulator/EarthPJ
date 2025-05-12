$(document).ready(function () {
    // Initially hide all optional sections
    hideAllSections();

    // Variable Selection
    let previousVariable = null;
    $('input[name="variable"]').click(function() {
        let $this = $(this);
        let variable = $this.val();

        // If clicking the same radio button
        if (variable === previousVariable) {
            $this.prop('checked', false);
            previousVariable = null;
            hideAllSections();
        } else {
            previousVariable = variable;
            showPlotTypes(variable);
        }
    });

    // Plot Type Selection
    let previousPlotType = null;
    $('input[name="graphVariable"]').click(function() {
        let $this = $(this);
        let plotType = $this.val();

        // If clicking the same radio button
        if (plotType === previousPlotType) {
            $this.prop('checked', false);
            previousPlotType = null;
            hideOptionsAfterPlotType();
        } else {
            previousPlotType = plotType;
            showOptionsForPlotType(plotType);
        }
    });

    // Time Period Type Selection
    $('input[name="graphType"]').change(function() {
        if ($(this).val() === 'single') {
            $(".compare-time").hide();
            $(".single-time").show();
        } else {
            $(".single-time").hide();
            $(".compare-time").show();
        }
    });

    function hideAllSections() {
        $(".plot-types").hide();
        $(".temperature-plots").hide();
        $(".precipitation-plots").hide();
        hideOptionsAfterPlotType();
    }

    function hideOptionsAfterPlotType() {
        $(".time-period-selection").hide();
        $(".single-time").hide();
        $(".compare-time").hide();
        $(".color-selection").parent().parent().hide();
        $(".month-bubble").hide();
        $(".region-selection").hide();
        $(".tempElev.options").hide();
        $(".spatial-options").hide();
        $(".toggle-container").hide();
    }

    function showPlotTypes(variable) {
        $(".plot-types").show();
        $(".temperature-plots, .precipitation-plots").hide();
        $(`.${variable}-plots`).show();
        hideOptionsAfterPlotType();
    }

    function showOptionsForPlotType(plotType) {
        // Show time period selection for non-time-series plots
        if (!plotType.includes('TimeSeries')) {
            $(".time-period-selection").show();
            if ($('input[name="graphType"]:checked').val() === 'single') {
                $(".single-time").show();
            } else {
                $(".compare-time").show();
            }
        }

        // Show/hide color selection
        const needsColorSelection = ['tempSfc', 'tempElev', 'pcpRate'].includes(plotType);
        $(".color-selection").parent().parent().toggle(needsColorSelection);

        // Show/hide month selection
        const needsMonthSelection = ['tempSfc', 'tempElev', 'pcpRate', 'longLatMonth'].includes(plotType);
        $(".month-bubble").toggle(needsMonthSelection);

        // Show/hide region selection
        const needsRegionSelection = ['tempSfc', 'tempElev', 'pcpRate', 'longLatMonth', 
                                    'globalTempAvg', 'globalPrecipAvg', 
                                    'tempTimeSeries', 'precipTimeSeries'].includes(plotType);
        $(".region-selection").toggle(needsRegionSelection);

        // Show/hide elevation selector
        $(".tempElev.options").toggle(plotType === 'tempElev');

        // Show standard deviation selection for appropriate plots
        $(".spatial-options").toggle(['tempSfc', 'tempElev', 'pcpRate'].includes(plotType));

        // Show percentage toggle for appropriate plots
        $(".toggle-container").toggle(['pcpRate', 'precipTimeSeries'].includes(plotType));
    }

    // Handle coordinate input validation
    $('.coordinate-inputs input[type="number"]').on('change', function() {
        var min_lat = parseFloat($('#min_latitude').val()) || -90;
        var max_lat = parseFloat($('#max_latitude').val()) || 90;
        var min_lon = parseFloat($('#min_longitude').val()) || -180;
        var max_lon = parseFloat($('#max_longitude').val()) || 180;

        // Validate and constrain values
        min_lat = Math.max(-90, Math.min(90, min_lat));
        max_lat = Math.max(-90, Math.min(90, max_lat));
        min_lon = Math.max(-180, Math.min(180, min_lon));
        max_lon = Math.max(-180, Math.min(180, max_lon));

        // Update input values
        $('#min_latitude').val(min_lat);
        $('#max_latitude').val(max_lat);
        $('#min_longitude').val(min_lon);
        $('#max_longitude').val(max_lon);
    });
});