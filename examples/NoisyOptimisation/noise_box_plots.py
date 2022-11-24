import numpy as np
from matplotlib import pyplot as plt

def plot_gp_model_versus_data(BoxPlotData, target_predictions, std_predictions):
    figure, axs = plt.subplots()

    try:
        axs.boxplot(BoxPlotData, labels=['n=1e4', 'n=2e4', 'n=3e4',
                                         'n=4e4', 'n=5e4'],
                    medianprops={'color': 'k'})
    except ValueError:
        print(f'couldnt label boxplots, label length didnt match data')
        axs.boxplot(BoxPlotData, medianprops={'color': 'k'})

    for i, data in enumerate(BoxPlotData.T):
        axs.scatter(np.ones(np.shape(data)[0]) * i + 1, data)
    axs.set_ylabel('OF')
    axs.set_title('Objective function values')

    # now add the predictions
    x_vals = np.arange(1, std_predictions.shape[0]+1)
    line1 = axs.plot(x_vals, -1*target_predictions, 'C6')
    axs.set_xlabel('Iteration number', fontsize=12)
    axs.set_ylabel('Objective function', fontsize=12)
    line2 = axs.fill_between(x_vals, -1*target_predictions + std_predictions,
                     -1*target_predictions - std_predictions, alpha=0.15, color='C0')
    axs.legend([line1[0], line2], ['Gaussian Process predictions', r'$\sigma$'], fontsize=12)
    axs.grid()
    plt.show()