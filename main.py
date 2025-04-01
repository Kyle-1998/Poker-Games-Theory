import clairvoyance
from game_trainer.algorithms import cfr
from game_trainer.trainer import Trainer
import visualiser

ante = 1
bet_size = 1

game = clairvoyance.Clairvoyance(ante, bet_size)
trainer = Trainer(game, cfr)

infosets, expected_utility, metrics_history = trainer.train(iterations=1000, display_results=False, display_freq=1, save_results=True, save_freq=100)

plot_config = game.get_plot_config()
fig = visualiser.plot_metrics_subplots(metrics_history, plot_config)
fig.show()


bet_sizes = [0.25, 0.33, 0.5, 0.66, 0.75, 1, 1.5, 2, 5, 10, 50, 100]

for bet_size in bet_sizes:
    game = clairvoyance.Clairvoyance(ante=1, bet_size=bet_size)
    trainer = Trainer(game, cfr)
    
    infosets, expected_utility, metrics_history = trainer.train(iterations=1000, display_results=False, save_results=True, save_freq=100)
    print(f"{'{0:,.2f}'.format(bet_size/(2*ante))}x pot: ",'{0:,.2f}'.format(infosets['Q-0'].get_average_strategy()[1]))
