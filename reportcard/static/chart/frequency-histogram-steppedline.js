function createConfig(details, data) {
			return {
				type: 'line',
				data: {
					labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6'],
					datasets: [{
						label: 'steppedLine: ' + details.steppedLine,
						steppedLine: details.steppedLine,
						data: data,
						borderColor: details.color,
						fill: false,
					}]
				},
				options: {
					responsive: true,
					title: {
						display: true,
						text: details.label,
					}
				}
			};
		}


		window.onload = function() {
			var container = document.querySelector('.frequency-histogram');

			/* two methods to get actual JSON
			via AJAX API call -- used dummy data for now from http://0.0.0.0:5000/frequency?rt=87&stop_id=87&period=history
			or pass from stop.html direct with template tag <script>createConfig({{hourly_frequency|tojson}})</script>
			*/
			var data = [
				{hour: '0', frequency: '60.0'},
				{hour: '1', frequency: '90.0'},
				{hour: '2', frequency: '0.0'},
				{hour: '3', frequency: '0.0'},
				{hour: '4', frequency: '0.0'},
				{hour: '5', frequency: '240.0'},
				{hour: '6', frequency: '40.0'},
				{hour: '7', frequency: '20.0'},
				{hour: '8', frequency: '15.0'},
				{hour: '9', frequency: '15.0'},
				{hour: '10', frequency: '20.0'},
				{hour: '11', frequency: '35.0'},
				{hour: '12', frequency: '45.0'},
				{hour: '13', frequency: '45.0'},
				{hour: '14', frequency: '55.0'},
				{hour: '15', frequency: '45.0'},
				{hour: '16', frequency: '30.0'},
				{hour: '17', frequency: '20.0'},
				{hour: '18', frequency: '20.0'},
				{hour: '19', frequency: '45.0'},
				{hour: '20', frequency: '45.0'},
				{hour: '21', frequency: '55.0'},
				{hour: '22', frequency: '60.0'},
				{hour: '23', frequency: '90.0'},
			];

			var steppedLineSettings = [{
				steppedLine: false,
				label: 'No Step Interpolation',
				color: window.chartColors.red
			}, {
				steppedLine: true,
				label: 'Step Before Interpolation',
				color: window.chartColors.green
			}, {
				steppedLine: 'before',
				label: 'Step Before Interpolation',
				color: window.chartColors.green
			}, {
				steppedLine: 'after',
				label: 'Step After Interpolation',
				color: window.chartColors.purple
			}];

			steppedLineSettings.forEach(function(details) {
				var div = document.createElement('div');
				div.classList.add('chart-container');

				var canvas = document.createElement('canvas');
				div.appendChild(canvas);
				container.appendChild(div);

				var ctx = canvas.getContext('2d');
				var config = createConfig(details, data);
				new Chart(ctx, config);
			});
		};