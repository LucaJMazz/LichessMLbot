import { request } from 'undici'
import 'dotenv/config';
import { EventEmitter } from 'events'
export const gameEvents = new EventEmitter()

var key = process.env.LICHESS_API_KEY;
var gameId = null;
var fen = '';
var moves = [];
var gameStatus = '';
var turn = false;
var color = ''

/**
 * Starts searching for games with API key
 * Runs on server start
 */
async function startGameSearch() {
    const { body } = await request('https://lichess.org/api/stream/event', { // Gets stream from Lichess
        headers: {
            Authorization: 'Bearer ' + key,
        }
    })
    
    for await (const chunk of body) { // Gets chunks coming in from the stream
        let streamChunk = chunk.toString().trim();
        if (!streamChunk) continue; 
        
        const data = JSON.parse(streamChunk); // Parse chunk as a readable JSON

        if (data.error) { // Error in data Fetching
            throw new Error("Error Fetching Game: " + data.error);
        }
        console.log("STREAM NEW GAMES:", data);

        const {game} = data;
        gameId = game.gameId;
        fen = game.fen;
        color = game.color;
        turn = game.isMyTurn;
        startCurrentStream();
    }
}

/**
 * Starts streaming game data
 * Runs once a game is found
 */
async function startCurrentStream() {
    const { statusCode, body } = await request(`https://lichess.org/api/bot/game/stream/${gameId}`, { // Gets game stream from Lichess
        headers: {
            Authorization: 'Bearer ' + key,
        }
    })

    if (statusCode !== 200) { // Error code
        throw new Error();
    }

    for await (const chunk of body) { // Gets chunks coming in from the stream
        let streamChunk = chunk.toString().trim();
        if (!streamChunk) continue;

        const data = JSON.parse(streamChunk);

        if (data.error) { // Error in data Fetching
            throw new Error("Error Fetching Game: " + data.error);
        }
        console.log("STREAM CURRENT:", data);

        let newMoves = []; // Gets moves from stream
        let newGameStatus = ''

        let state = data.state;
        if (!state) state = data;
        if (state.type == 'gameState') {
            newMoves = state.moves.split(' ');
            newGameStatus = state.status;
        } else {
            console.log("No incoming moves founnd");
        }

        if (newMoves.join(' ') !== moves.join(' ')) { // If the moves are different from previous list
            moves = newMoves;
            gameStatus = newGameStatus;
            turn = color === 'white' 
                    ? moves.length % 2 === 0
                    : moves.length % 2 === 1
            gameEvents.emit('move', { moves, gameStatus, turn });
            console.log('updated moves');
        }
    }
}

export async function postMove(move) {
    try {
                const { statusCode, body } = await request(
            `https://lichess.org/api/bot/game/${gameId}/move/${move}`,
            {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + key,
                }
            }
        );

        const responseText = body ? await body.text() : '';

        return {
            ok: statusCode === 200,
            status: statusCode,
            body: responseText
        };

    } catch (err) {
        return {
            ok: false,
            error: err.message
        };
    }
}

/**
 * Gets moves from Lichess stream
 * @returns Move list as array
 */
export function getMoves() {
    return moves;
}

/**
 * Gets game status from lichess stream
 * @returns Game status: started, draw, checkmate etc.
 */
export function getStatus() {
    return gameStatus;
}

/**
 * Gets turn from boolean variable
 * @returns True if it is the players turn
 */
export function getTurn() {
    return turn;
}

/**
 * Gets fen from lichess game
 * @returns fen as a string
 */
export function getFen() {
    return fen;
}

/**
 * Gets colour from lichess game
 * @returns Bots color
 */
export function getColor() {
    return color;
}


startGameSearch();
