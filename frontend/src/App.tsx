import { useState } from 'react';
import { useSnapshot } from './useSnapshot'
import { useHistory } from './useHistory';
import PlayerChart from './PlayerChart';
import PlayerHistoryChart from './PlayerHistoryChart';
import PlayerTable from './PlayerTable';
import './App.css';
import { figure_width } from './constants';

export default function App() {
  const state = useSnapshot();
  const history = useHistory();

  const [selectedId, setSelectedId] = useState<number | null>(null);

  if (state.status === 'loading') return <div>Loading...</div>;
  if (state.status === 'error') return <div>Error: {state.message}</div>;

  const selectedPlayer = selectedId != null
    ? state.players.players.find((p) => p.nba_id === selectedId)
    : undefined;
  const selectedHistory = selectedId != null
    ? history?.series[String(selectedId)]
    : undefined;

  return (
    <div className='page-container'>
      <main>
        <div className='text'>
          <header>
            <div className='title'>
              <h1>paid to play</h1>
              <strong>by <a href='https://www.sanchezner.com' target='_blank'>sanchezner orange</a></strong>
            </div>
              <p>{state.players.season}</p>
          </header>
          <h2>what this is</h2>
          <p>
            Every dot is an NBA player this season with {'>'}20 games played. The further right, the better our model expects them to perform; the higher up, the bigger the bite their salary takes out of their team's cap. The dashed line is the league-wide trend (from 1999 to present) of what teams, in aggregate, actually pay for a given level of expected production.
          </p>
          <p>
            This is descriptive trend, not a verdict on what any player "should" earn. A player far from the line isn't mispriced by some cosmic law; they're priced differently than the league norm, which is often the case (injury history, age, contract timing) and sometimes genuinely surprising.
          </p>

          <h2>metrics defined</h2>
          <p>
            <strong>predicted BPM (pBPM)</strong> - our model's estimate of a player's Box Plus-Minus: net points contributed per 100 possessions versus a league-average player.
          </p>
          <p>
            <strong>cap %</strong> - the player's salary as a share of the salary cap. Comparing across seasons in cap terms, not dollars, keeps eras comparable.
          </p>
          <p>
            <strong>value vs. trend</strong> - the gap between a player's actual cap hit and what the trend line pays for their predicted production. <span className='positive-text'>Positive</span> means paid above the trend; <span className='negative-text'>negative</span> means paid below it.
          </p>

          <h2>how to explore</h2>
          <p>
            Search or sort the table, and click a row to spotlight that player in the chart and show their season pBPM progression. A few familiar (and mildly interesting) names are labeled to get you started.
          </p>
        </div>
        <div className={`figures${selectedId != null ? ' figures--selected' : ''}`}>
          <div className='chart'>
            <PlayerChart players={state.players.players} curvePoints={state.curve.points} selectedId={selectedId} />
          </div>
          {selectedPlayer && selectedHistory && selectedHistory.length > 0 && (
            <div className='history-chart'>
              <PlayerHistoryChart name={selectedPlayer.name} points={selectedHistory} />
            </div>
          )}
          <div className='table' style={{ width: figure_width, maxWidth: '100%' }}>
            <PlayerTable players={state.players.players} selectedId={selectedId} onSelectPlayer={setSelectedId} />
          </div>
          <p className='data-sources'>
            Sources:{' '}
            <a href='https://github.com/swar/nba_api' target='_blank' rel='noreferrer'>NBA API</a>
            {', '}
            <a href='https://www.basketball-reference.com' target='_blank' rel='noreferrer'>Basketball Reference</a>
            {', '}
            <a href='https://www.espn.com/nba/salaries' target='_blank' rel='noreferrer'>ESPN Salaries</a>
            {', '}
            <a href='https://www.wikidata.org' target='_blank' rel='noreferrer'>Wikidata</a>
          </p>
        </div>
      </main>
    </div>
  );
}

