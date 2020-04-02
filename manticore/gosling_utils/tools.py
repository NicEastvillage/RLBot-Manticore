from gosling_utils.routines import *

#This file is for strategic tools

def find_hits(agent,targets):
    #find_hits takes a dict of (left,right) target pairs and finds routines that could hit the ball between those target pairs
    #find_hits is only meant for routines that require a defined intercept time/place in the future
    #find_hits should not be called more than once in a given tick, as it has the potential to use an entire tick to calculate

    #Example Useage:
    #targets = {"goal":(opponent_left_post,opponent_right_post), "anywhere_but_my_net":(my_right_post,my_left_post)}
    #hits = find_hits(agent,targets)
    #print(hits)
    #>{"goal":[a ton of jump and aerial routines,in order from soonest to latest], "anywhere_but_my_net":[more routines and stuff]}
    hits = {name:[] for name in targets}
    struct = agent.get_ball_prediction_struct()
    
    #Begin looking at slices 0.25s into the future
    #The number of slices 
    i = 15
    while i < struct.num_slices:
        #Gather some data about the slice
        intercept_time = struct.slices[i].game_seconds
        time_remaining = intercept_time - agent.time
        if time_remaining > 0:
            ball_location = Vector3(struct.slices[i].physics.location)
            ball_velocity = Vector3(struct.slices[i].physics.velocity).magnitude()

            if abs(ball_location[1]) > 5250:
                break #abandon search if ball is scored at/after this point
        
            #determine the next slice we will look at, based on ball velocity (slower ball needs fewer slices)
            i += 15 - cap(int(ball_velocity//150),0,13)
            
            car_to_ball = ball_location - agent.me.location
            #Adding a True to a vector's normalize will have it also return the magnitude of the vector
            direction, distance = car_to_ball.normalize(True)

            #How far the car must turn in order to face the ball, for forward and reverse
            forward_angle = direction.angle(agent.me.orientation.forward)
            backward_angle = math.pi - forward_angle

            #Accounting for the average time it takes to turn and face the ball
            #Backward is slightly longer as typically the car is moving forward and takes time to slow down
            forward_time = time_remaining - (forward_angle * 0.318)
            backward_time = time_remaining - (backward_angle * 0.418)

            #If the car only had to drive in a straight line, we ensure it has enough time to reach the ball (a few assumptions are made)
            forward_flag = forward_time > 0.0 and (distance*1.05 / forward_time) < (2290 if agent.me.boost > distance/100 else 1400)
            backward_flag = distance < 1500 and backward_time > 0.0 and (distance*1.05 / backward_time) < 1200
            
            #Provided everything checks out, we begin to look at the target pairs
            if forward_flag or backward_flag:
                for pair in targets:
                    #First we correct the target coordinates to account for the ball's radius
                    #If swapped == True, the shot isn't possible because the ball wouldn't fit between the targets
                    left,right,swapped = post_correction(ball_location,targets[pair][0],targets[pair][1])
                    if not swapped:
                        #Now we find the easiest direction to hit the ball in order to land it between the target points
                        left_vector = (left - ball_location).normalize()
                        right_vector = (right - ball_location).normalize()
                        best_shot_vector = direction.clamp(left_vector,right_vector)
                        
                        #Check to make sure our approach is inside the field
                        if in_field(ball_location - (200*best_shot_vector),1):
                            #The slope represents how close the car is to the chosen vector, higher = better
                            #A slope of 1.0 would mean the car is 45 degrees off
                            slope = find_slope(best_shot_vector,car_to_ball)
                            if forward_flag:
                                if ball_location[2] <= 300 and slope > 0.0:
                                    hits[pair].append(jump_shot(ball_location,intercept_time,best_shot_vector,slope))
                                if ball_location[2] > 300 and ball_location[2] < 600 and slope > 1.0 and (ball_location[2]-250) * 0.14 > agent.me.boost:
                                    hits[pair].append(aerial_shot(ball_location,intercept_time,best_shot_vector,slope))
                            elif backward_flag and ball_location[2] <= 280 and slope > 0.25:
                                hits[pair].append(jump_shot(ball_location,intercept_time,best_shot_vector,slope,-1))
    return hits


def decide_kickoff_strategy(agent):
    allies = agent.friends + [agent.me]
    corner = [friend for friend in allies if abs(friend.location.y) < 3000]
    back_corner = [friend for friend in allies if 3000 < abs(friend.location.y) < 4000]
    back = [friend for friend in allies if 4000 < abs(friend.location.y)]
    big_pads = [pad for pad in agent.boosts if pad.large and pad.active]
    if agent.me in corner:
        if len(corner) < 2 or side(agent.team) * agent.me.location.x < 0:
            # Corner kickoff
            agent.push(kickoff())
        else:
            # Tied for corner kickoff
            agent.push(second_man_kickoff())
    elif len(corner) > 0:
        # Someone else is in the corner
        if agent.me in back_corner or len(back_corner) == 0:
            # Collect closest big boost pad
            pad, _ = argmin(big_pads, lambda pad: pad.location.dist(agent.me.location))
            agent.push(goto_boost(pad, agent.friend_goal.location, may_flip=False))
        else:
            # We are back and someone is back corner and corner
            pad = [pad for pad in big_pads if pad.location.y * side(agent.team) > 100 and sign(pad.location.x) != sign(back_corner[0].location.x)][0]
            agent.push(goto_boost(pad, agent.ball.location, may_flip=False))
    # No one has corner
    elif agent.me in back_corner:
        if len(back_corner) < 2 or side(agent.team) * agent.me.location.x < 0:
            # Corner kickoff
            agent.push(kickoff())
        else:
            # Tied for corner kickoff
            agent.push(second_man_kickoff())
    elif len(back_corner) == 1:
        agent.push(second_man_kickoff())
    elif len(back_corner) == 2:
        pad = [pad for pad in big_pads if pad.location.y * side(agent.team) > 100 and sign(pad.location.x) != side(agent.team)][0]
        agent.push(goto_boost(pad, agent.ball.location, may_flip=False))
    else:
        # We are alone
        agent.push(kickoff())
