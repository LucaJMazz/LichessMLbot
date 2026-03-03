import { request } from 'undici'
import 'dotenv/config';

var key = process.env.LICHESS_API_KEY;
var game = null;
var gameId = null;
var moves = [];

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

        game = data; // Saves game as JSON
        gameId = data.game.gameId; // Sets the current Game ID
        startMoveStream();
    }
}

/**
 * Starts streaming game data
 * Runs once a game is found
 */
async function startMoveStream() {
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

        // 2 versions of data.type, one occurs at the start of the stream
        if (data.type == 'gameState') {  
            newMoves = data.moves.split(' '); 
        }
        else if (data.state.type == 'gameState') {
            newMoves = data.state.moves.split(' ');
        } else {
            throw new Error("No incoming moves founnd");
        }

        if (newMoves.join(' ') !== moves.join(' ')) { // If the moves are different from previous list
            moves = newMoves;
            console.log('updated moves');
        }
    }
}

export async function postMove(move) {
    const { statusCode, body } = await request(`https://lichess.org/api/bot/game/${gameId}/move/${move}`, {
        method: 'POST',
        headers: {
            Authorization: 'Bearer ' + key,
        }
    })

    try {
        if (statusCode !== 200) { // Error code
            throw new Error("Illegal Move Argument ", statusCode);
        }
    } catch {

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
 * Gets game data from Lichess stream
 * @returns Game data as JSON
 */
export function getGame() {
    return game;
}



startGameSearch();
